{ self, nixpkgs, ... }:
nixpkgs.lib.nixosSystem {
  system = "x86_64-linux";
  pkgs = import nixpkgs {
    system = "x86_64-linux";
    overlays = [
      self.overlays.worblehat
    ];
  };
  modules = [
    "${nixpkgs}/nixos/modules/virtualisation/qemu-vm.nix"
    "${nixpkgs}/nixos/tests/common/user-account.nix"

    self.nixosModules.default

    ({ config, ... }: {
      system.stateVersion = config.system.nixos.release;
      virtualisation.graphics = false;

      users.motd = ''
        =================================
        Welcome to the worblehat non-kiosk vm!

        Try running:
            ${config.services.worblehat.package.meta.mainProgram} cli

        Password for worblehat is 'worblehat'

        To exit, press Ctrl+A, then X
        =================================
      '';

      users.users.worblehat = {
        isNormalUser = true;
        password = "worblehat";
        extraGroups = [ "wheel" ];
      };

      services.getty.autologinUser = "worblehat";

      programs.vim = {
        enable = true;
        defaultEditor = true;
      };

      services.postgresql.enable = true;

      services.worblehat = {
        enable = true;
        createLocalDatabase = true;
      };
    })
  ];
}
