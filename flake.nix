{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    libdib.url = "git+https://git.pvv.ntnu.no/Projects/libdib.git";
    libdib.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = inputs@{ self, nixpkgs, ... }: let
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: let
      pkgs = import nixpkgs {
        inherit system;
        overlays = [
          inputs.libdib.overlays.default
        ];
      };
    in f system pkgs);

    inherit (nixpkgs) lib;

    deps = ppkgs: with ppkgs; [
      alembic
      beautifulsoup4
      click
      flask
      (flask-admin.override {
        wtf-peewee = wtf-peewee.overrideAttrs (_: {
          doCheck = false;
          doInstallCheck = false;
        });
      })
      flask-sqlalchemy
      isbnlib
      libdib
      psycopg2-binary
      python-dotenv
      requests
      sqlalchemy
    ];

  in {
    apps = forAllSystems (system: pkgs: let
      mkApp = package: {
        type = "app";
        program = lib.getExe package;
      };
    in {
      default = mkApp self.packages.${system}.default;
    });

    devShells = forAllSystems (_: pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs; [
          uv
          ruff
          sqlite-interactive
          (python3.withPackages deps)
        ];
      };
    });

    overlays.default = final: prev: self.packages.${final.system};

    packages = forAllSystems (system: pkgs: {
      default = self.packages.${system}.worblehat;
      worblehat = let
        inherit (pkgs) python3Packages;
        pyproject = lib.pipe ./pyproject.toml [
          builtins.readFile
          builtins.fromTOML
        ];
      in python3Packages.buildPythonApplication {
        pname = pyproject.project.name;
        version = pyproject.project.version;
        src = lib.cleanSource ./.;

        format = "pyproject";

        build-system = with python3Packages; [ hatchling ];
        dependencies = deps pkgs.python3Packages;

        meta.mainProgram = "worblehat";
      };
    });
  };
}
