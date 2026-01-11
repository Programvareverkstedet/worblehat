{ config, pkgs, lib, ... }: let
  cfg = config.services.worblehat;

  format = pkgs.formats.toml { };
in {
  options.services.worblehat = {
    enable = lib.mkEnableOption "worblehat, the little kiosk library";

    package = lib.mkPackageOption pkgs "worblehat" { };

    screenPackage = lib.mkPackageOption pkgs "screen" { };

    createLocalDatabase = lib.mkEnableOption "" // {
      description = ''
        Whether to set up a local postgres database automatically.

        ::: {.note}
        You must set up postgres manually before enabling this option.
        :::
      '';
    };

    kioskMode = lib.mkEnableOption "" // {
      description = ''
        Whether to let worblehat take over the entire machine.

        This will restrict the machine to a single TTY and make the program unquittable.
        You can still get access to PTYs via SSH and similar, if enabled.
      '';
    };

    limitScreenHeight = lib.mkOption {
      type = with lib.types; nullOr ints.unsigned;
      default = null;
      example = 42;
      description = ''
        If set, limits the height of the screen worblehat uses to the given number of lines.
      '';
    };

    limitScreenWidth = lib.mkOption {
      type = with lib.types; nullOr ints.unsigned;
      default = null;
      example = 80;
      description = ''
        If set, limits the width of the screen worblehat uses to the given number of columns.
      '';
    };

    settings = lib.mkOption {
      description = "Configuration for worblehat";
      default = { };
      type = lib.types.submodule {
        freeformType = format.type;
      };
    };
  };

  config = lib.mkIf cfg.enable (lib.mkMerge [
    {
      services.worblehat.settings = lib.pipe ../config-template.toml [
        builtins.readFile
        builtins.fromTOML
        (x: lib.recursiveUpdate x {
          flask = {
            TESTING = false;
            DEBUG = false;
          };
        })
        (lib.mapAttrsRecursive (_: lib.mkDefault))
      ];
    }
    {
      environment.systemPackages = [ cfg.package ];

      environment.etc."worblehat/config.toml".source = format.generate "worblehat-config.toml" cfg.settings;

      users = {
        users.worblehat = {
          group = "worblehat";
          isNormalUser = true;
        };
        groups.worblehat = { };
      };

      services.worblehat.settings.database.type = "postgresql";
      services.worblehat.settings.database.postgresql = {
        host = "/run/postgresql";
      };

      services.postgresql = lib.mkIf cfg.createLocalDatabase {
        ensureDatabases = [ "worblehat" ];
        ensureUsers = [{
          name = "worblehat";
          ensureDBOwnership = true;
          ensureClauses.login = true;
        }];
      };

      systemd.services.worblehat-setup-database = lib.mkIf cfg.createLocalDatabase {
        description = "Dibbler database setup";
        wantedBy = [ "default.target" ];
        after = [ "postgresql.service" ];
        unitConfig = {
          ConditionPathExists = "!/var/lib/worblehat/.db-setup-done";
        };
        serviceConfig = {
          Type = "oneshot";
          ExecStart = "${lib.getExe cfg.package} --config /etc/worblehat/config.toml create-db";
          ExecStartPost = "${lib.getExe' pkgs.coreutils "touch"} /var/lib/worblehat/.db-setup-done";
          StateDirectory = "worblehat";

          User = "worblehat";
          Group = "worblehat";
        };
      };
    }
    (lib.mkIf cfg.kioskMode {
      boot.kernelParams = [
        "console=tty1"
      ];

      users.users.worblehat = {
        extraGroups = [ "lp" ];
        shell = (pkgs.writeShellScriptBin "login-shell" "${lib.getExe cfg.screenPackage} -x worblehat") // {
          shellPath = "/bin/login-shell";
        };
      };

      services.worblehat.settings.general = {
        quit_allowed = false;
        stop_allowed = false;
      };

      systemd.services.worblehat-screen-session = {
        description = "Worblehat Screen Session";
        wantedBy = [
          "default.target"
        ];
        after = if cfg.createLocalDatabase then [
          "postgresql.service"
          "worblehat-setup-database.service"
        ] else [
          "network.target"
        ];
        serviceConfig = {
          Type = "forking";
          RemainAfterExit = false;
          Restart = "always";
          RestartSec = "5s";
          SuccessExitStatus = 1;

          User = "worblehat";
          Group = "worblehat";

          ExecStartPre = "-${lib.getExe cfg.screenPackage} -X -S worblehat kill";
          ExecStart = let
            screenArgs = lib.escapeShellArgs [
              # -dm creates the screen in detached mode without accessing it
              "-dm"

              # Session name
              "-S"
              "worblehat"

              # Set optimal output mode instead of VT100 emulation
              "-O"

              # Enable login mode, updates utmp entries
              "-l"
            ];

            worblehatArgs = lib.cli.toCommandLineShellGNU { } {
              config = "/etc/worblehat/config.toml";
            };

          in "${lib.getExe cfg.screenPackage} ${screenArgs} ${lib.getExe cfg.package} ${worblehatArgs} cli";
          ExecStartPost =
            lib.optionals (cfg.limitScreenWidth != null) [
              "${lib.getExe cfg.screenPackage} -X -S worblehat width ${toString cfg.limitScreenWidth}"
            ]
            ++ lib.optionals (cfg.limitScreenHeight != null) [
              "${lib.getExe cfg.screenPackage} -X -S worblehat height ${toString cfg.limitScreenHeight}"
            ];
        };
      };

      services.getty.autologinUser = "worblehat";
    })
  ]);
}
