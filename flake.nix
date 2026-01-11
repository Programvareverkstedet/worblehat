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
      mkApp = program: description: {
        type = "app";
        program = toString program;
        meta = {
          inherit description;
        };
      };
      mkVm = name: mkApp "${self.nixosConfigurations.${name}.config.system.build.vm}/bin/run-nixos-vm";
    in {
      default = self.apps.${system}.worblehat;
      worblehat = mkApp (lib.getExe self.packages.${system}.worblehat) "Run worblehat without any setup";
      vm = mkVm "vm" "Start a NixOS VM with worblehat installed in kiosk-mode";
      vm-non-kiosk = mkVm "vm-non-kiosk" "Start a NixOS VM with worblehat installed in nonkiosk-mode";
    });

    nixosModules.default = import ./nix/module.nix;

    nixosConfigurations = {
      vm = import ./nix/nixos-configurations/vm.nix { inherit self nixpkgs; };
      vm-non-kiosk = import ./nix/nixos-configurations/vm-non-kiosk.nix { inherit self nixpkgs; };
    };

    overlays = {
      default = self.overlays.worblehat;
      worblehat = final: prev: {
        inherit (self.packages.${prev.stdenv.hostPlatform.system}) worblehat;
      };
    };

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
