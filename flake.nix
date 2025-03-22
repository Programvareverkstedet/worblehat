{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }: let
    systems = [
      "x86_64-linux"
      "aarch64-linux"
      "x86_64-darwin"
      "aarch64-darwin"
    ];

    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
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
      worblehat = with pkgs.python3Packages; buildPythonPackage {
        pname = "worblehat";
        version = "0.1.0";
        src = ./.;

        format = "pyproject";

        build-system = [ hatchling ];
        dependencies = deps pkgs.python3Packages;

        meta.mainProgram = "worblehat";
      };
    });
  };
}
