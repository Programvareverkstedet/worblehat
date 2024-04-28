{
  inputs.nixpkgs.url = "nixpkgs/nixos-23.11";

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
  in {
    apps = forAllSystems (system: pkgs: let
      mkApp = program: {
        type = "app";
        inherit program;
      };
    in {
      default = mkApp self.packages.${system}.default;
    });

    devShells = forAllSystems (_: pkgs: {
      default = pkgs.mkShell {
        packages = with pkgs; [
          poetry
          sqlite
        ];
        shellHook = ''
          poetry install
          poetry shell && exit
        '';
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

        buildInputs = [ poetry-core ];
        propagatedBuildInputs = [
          alembic
          click
          flask
          flask-admin
          flask-sqlalchemy
          isbnlib
          python-dotenv
          sqlalchemy
        ];
      };
    });
  };
}
