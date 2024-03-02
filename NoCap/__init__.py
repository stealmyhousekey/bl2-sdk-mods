import unrealsdk
import bl2sdk
from typing import Dict, Optional, Any, cast
import Mods.ModMenu as ModMenu
from Mods.UserFeedback import TextInputBox, OptionBox, OptionBoxButton
from Mods.ModMenu import (Mods, EnabledSaveType, Game, Keybind, KeybindManager, ModTypes, Options, SDKMod, Hook, RegisterMod, ClientMethod, ServerMethod)
from Mods.NoCap.lxcbl2 import (get_pc, is_host, is_client, log, logc, logf, get_vaulthunter_class, get_world_info, get_weapon_holding, console_command, get_obj_path_name, obj_is_in_class, feedback)

#! deprecated imports
# from ModMenu.KeybindManager import Keybind
# from Mods.Enums import ENetMode, EModifierType

class NoCap(ModMenu.SDKMod):
    Name: str = "NoCap"
    Author: str = "stelmo"
    Description: str = "uncaps lobby size and allows up to 8 teams (by default)\n\nshoutouts to robeth for his cooppatch and great documentation\n\n[fax, no printer]"
    Version: str = "0.1.1"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2 | ModMenu.Game.TPS  # Either BL2 or TPS; bitwise OR'd together
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Gameplay  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadOnMainMenu


    def Enable(self) -> None:
        super().Enable()
        #^ enddef Enable
        

    def Disable(self) -> None:
        super().Disable()
        #^ enddef Disable


    def ModOptionChanged(self, option, new_value: Any) -> None:
        if new_value:
            if option == self.TeamCount:
                self.set_uncapped_lobby(new_value)

            if option == self.EnableNetTweaks:
                    self.set_uncapped_networking()

            if option == self.EnableMaxScaling:
                self.set_uncapped_scaling()

        #^ enddef ModOptionChanged


    def __init__(self) -> None:
        ''' main constructor '''

        self.TeamCount = Options.Slider(
            Caption="Number of Teams",
            Description="Number of teams available in-game",
            StartingValue=2,
            MinValue=1,
            MaxValue=8,
            Increment=1,
        )

        self.EnableNetTweaks = Options.Boolean(
            Caption="Enable Networking Tweaks",
            Description="Optimize network traffic for 4+ players",
            StartingValue=True,
            Choices=("Off", "On"),
            IsHidden=False
        )

        self.EnableMaxScaling = Options.Boolean(
            Caption="Enable Maxed Scaling",
            Description="Enforce 4 player difficulty, even when less than 4 players are present on a team",
            StartingValue=False,
            Choices=("Off", "On"),
            IsHidden=False
        )

        self.EnableLogging = Options.Boolean(
			Caption="Enable Logging",
			Description=("Enables clientside console logging\n"
						"[BASE]"),
			StartingValue=True,
			Choices = ("Off", "On"),
			IsHidden=False
		)

        self.Keybinds = [
            Keybind(
                "NoCap Hotkey",
                "Period",
                True,
                OnPress=self.hotkey_nocap
            )
        ]

        self.Options = [
            self.TeamCount,
            self.EnableNetTweaks,
            self.EnableMaxScaling,
            self.EnableLogging
        ]

        self.player_loaded = False
        self.player_ready = False
        self.teams_dict = {}
        self.team_menu = None
        self.tweaks_applied = False
        self.awaiting_menu = False

        #^ enddef __init__

    
    def hotkey_nocap(self, event: KeybindManager.InputEvent) -> None:
        ''' called when hotkey is pressed '''
        if is_client():
            if event == KeybindManager.InputEvent.Released:
                log(self, "Requesting team info from host...")
                self.awaiting_menu = True
                unrealsdk.Log(self.net_teaminfo_request())
        #^ enddef hotkey_nocap


    # accept self as first arg and optional int as second
    def set_uncapped_lobby(self, new_value: Optional[int] = None) -> None:
        ''' sets game vars to uncap player count '''
        player_count = self.TeamCount.CurrentValue * 4
        if new_value is not None:
            player_count = new_value * 4
        PC = get_pc()
        if PC is not None:
            commands = [
                f"set WillowOnlineGameSettings NumPublicConnections {player_count}", # robeth val: 64
                "set GameInfo MaxPlayers 0", # TODO: cap this maybe? leaving at robeth val for now
                "set GameInfo MaxPlayersAllowed 512" # TODO: cap this maybe? leaving at robeth val for now
            ]
            for command in commands:
                PC.ServerRCon(command)
            log(self, "Lobby size adjusted to", player_count)
        #^ enddef set_uncapped_lobby


    def set_uncapped_scaling(self) -> None:
        ''' sets game var to max difficulty scaling for 4+ players'''
        PC = get_pc()
        if PC is not None:
            PC.ServerRCon(f"set Engine.GameInfo EffectiveNumPlayers 4") 
            log(self, "Lobby scaling adjusted")
        #^ enddef set_uncapped_scaling


    def set_uncapped_networking(self) -> None:
        ''' sets game vars to optimize net traffic for 4+ players '''
        PC = get_pc()
        if PC is not None:
            commands = [
                "set WillowCoopGameInfo TotalNetBandwidth 640000",
                "set WillowCoopGameInfo MinDynamicBandwidth 2000",
                "set PlayerInteractionServer TimeoutTime 60.0",
                "set GameInfo AdjustedNetSpeed 5000",
                "set IPDrv.TCPNetDriver NetServerMaxTickrate 20",
                "set IPDrv.TCPNetDriver bClampListenServerTickRate False",
                "set IPDrv.TCPNetDriver KeepAliveTime 0.500000",
                "set IPDrv.TCPNetDriver MaxInternetClientRate 7000",
                "set IPDrv.TCPNetDriver MaxClientRate 10000",
                "set IPDrv.TCPNetDriver SpawnPrioritySeconds 2",
                "set IPDrv.TCPNetDriver InitialConnectTimeout 300",
                "set IPDrv.TCPNetDriver ConnectionTimeout 120",
                "set WillowPlayerReplicationInfo NetUpdateFrequency 20",
                "set Engine NetClientTicksPerSecond 100.0",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks NetServerMaxTickRate 20",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks bClampListenServerTickRate False",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks KeepAliveTime 0.500000",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks MaxInternetClientRate 7000",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks MaxClientRate 10000",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks SpawnPrioritySeconds 2",
                "set OnlineSubsystemSteamworks.IpNetDriverSteamworks ConnectionTimeout 120"
            ]
            for command in commands:
                PC.ServerRCon(command)
            log(self, "Networking optimizations applied")
            #^ enddef set_uncapped_networking


    def build_teams_menu(self):
        ''' shows the lobby team menu '''
        sv_teams = 1
        btn1 = OptionBoxButton("Team 1")
        self.team_menu: OptionBox = OptionBox(
            PreventCanceling=True,
            Title="Current Teams",
            Caption="",
            Buttons=[btn1]
        )
        
        # parse sv_teams
        if self.teams_dict["sv_teams"] is not None:
            sv_teams = self.teams_dict["sv_teams"]

            # iterate through sv_teams (skipping 1, as it already exists) and add buttons
            for i in range(1, sv_teams):
                self.team_menu.Buttons.append(OptionBoxButton(f"Team {i+1}"))

            # handle button presses in the menu
            def _on_main_press(button: OptionBoxButton) -> None:
                '''internal function: called when a button is pressed'''
                for i, btn in enumerate(self.team_menu.Buttons):
                    if button == btn:
                        self.choose_team(i)
            self.team_menu.OnPress = _on_main_press
        #^ enddef build_teams_menu
    

    def build_team_string(self, teams: dict, teamid: int) -> str:
        ''' builds a single-line team string '''
        team_string = f"Team {(teamid + 1)}: "
        for player, team in teams.items():
            if team == teamid:
                team_string += f"{player}, "
        team_string = team_string[:-2] # remove trailing comma
        return team_string
        #^ enddef build_team_string
        

    def update_team_menu(self) -> None:
        ''' refreshes the team join menu '''

        if self.teams_dict["sv_teams"] is not None:
            sv_teams = self.teams_dict["sv_teams"]

        # Create a list to hold the team strings
        teams = []

        # Dynamically build team strings based on sv_teams
        for i in range(sv_teams):
            team = self.build_team_string(self.teams_dict, i)
            teams.append(team)

        # Join the team strings with newlines and set the caption
        self.team_menu.Caption = "\n".join(teams) + "\n"

        # log(self, "Updated team menu")
        self.team_menu.Update()
        self.team_menu.Show()
        #^ enddef update_team_menu


# region hooks

    # # this hook is too early, and numplayers is not updated yet
    # @Hook("WillowGame.WillowCoopGameInfo.PostLogin")
    # def post_login(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    #     ''' applies 4+ player tweaks on host; called after a 4th player logs in '''
    #     # log(self, "PostLogin called")
    #     if is_host():
    #         log(self, "Player logged in, current player count: ", this.NumPlayers)
    #         if this.NumPlayers >= 4:
    #             if not self.tweaks_applied:
    #                 self.tweaks_applied = True
    #                 self.set_uncapped_scaling()
    #                 self.set_uncapped_networking()
    #     return True
        
    # # called on host when client runs console command "changeteam" or when client joins
    # @Hook("WillowGame.WillowCoopGameInfo.ChangeTeam")
    # def change_team(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    #     # params: Controller Other, int N, bool bNewTeam
    #     log(self, "ChangeTeam called")
    #     return True


    def check_welcomed(self) -> bool:
        ''' checks if the client has been welcomed '''
        if is_client():
            pc = get_pc()
            if pc is not None:
                pri = pc.PlayerReplicationInfo
                if pri is not None:
                    if pri.bHasBeenWelcomed is not None:
                        return pri.bHasBeenWelcomed == True
        return False
        #^ enddef check_welcomed


    @Hook("WillowGame.WillowPlayerController.ShowLobbyUI")
    def joined_lobby(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:        
        '''called when client connects to host and reaches lobby, updated when player has been welcomed'''
        if is_client:
            pc: unrealsdk.UObject = this
            pawn: unrealsdk.UObject = pc.Pawn
            log(self, "Joined lobby and showing UI")
            self.player_loaded = False
            self.player_ready = False

            def tick(this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if(self.player_loaded == False):
                    if(self.check_welcomed()):
                        log(self, "Player has been welcomed")
                        self.player_loaded = True
                        if(self.player_ready == False):
                            self.player_ready = True
                            self.awaiting_menu = True
                            self.net_teaminfo_request()
                            unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.Tick", "lobby_tick")
                            # self._NetChangeTeam(5)
                return True 

            unrealsdk.RunHook("WillowGame.WillowGameViewportClient.Tick", "lobby_tick", tick)
        return True
        #^ enddef joined_lobby
    

    # initializeteams
    # called only on host? and host does not call any other team functions afaict
    @Hook("WillowGame.WillowCoopGameInfo.InitializeTeams")
    def initialize_teams(self, this: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        '''
        default:
            CreateTeam(0, "Players");
            CreateTeam(1, "AI");
        '''
        #* fallback to built-in method if team count is default (2)
        if(self.TeamCount.CurrentValue <= 2):
            return True

        #* create the original teams
        this.CreateTeam(0, "Players")
        this.CreateTeam(1, "AI")

        #* create x new teams, where x = TeamCount - 2
        for i in range(2, self.TeamCount.CurrentValue):
            this.CreateTeam(i, f"Players{i}")

        #? create lobby team to avoid lockout when team 0 is full

        #! do not allow original method to run
        return False
        #^ enddef initialize_teams


# endregion hooks


# region netmethod:teamchange

    def choose_team(self, choice: int) -> None:
        if (get_pc().PlayerReplicationInfo.Team.TeamIndex == choice):
            return
        else:
            log(self, "Chose Team: ", choice)
            self.net_changeteam(choice)
        #^ enddef choose_team


    def net_changeteam(self, team_num) -> None:
        if is_client():
            log(self, "Requesting client net_changeteam")
            self.net_changeteam_request(team_num)
        else:
            log(self, "Executing host net_changeteam")
            self.host_changeteam_execute(team_num)
        #^ enddef net_changeteam


    @ServerMethod
    def net_changeteam_request(self, team_num, PC: Optional[unrealsdk.UObject] = None, ) -> None:
        # logc(self, PC, " has started net_changeteam_request")
        self.host_changeteam_execute(team_num, PC)
        self.net_changeteam_response(team_num)
        #^ enddef net_changeteam_request


    @ClientMethod
    def net_changeteam_response(self, team_num: str) -> None:
        PC = get_pc()
        log(self, "Client received net_changeteam_response", team_num)
        #^ enddef net_changeteam_response


    def host_changeteam_execute(self, team_num, PC: Optional[unrealsdk.UObject] = None, ) -> None:
        if PC is None:
            PC = get_pc()
        log(self, "executing host_changeteam_execute")
        # logc(self, PC, "is executing host_changeteam_execute with value: ", team_num)
        self.host_changeteam(PC, team_num)
        #^ enddef host_changeteam_execute


    def host_changeteam(self, pc, team_num) -> None:
        coopgame = unrealsdk.FindAll("WillowCoopGameInfo")[-1]
        coopgame.ChangeTeam(pc, team_num, False)
        log(self, "Changed client team to", team_num)
        #^ enddef host_changeteam

# endregion

# region netmethod:teaminfo
        
    def host_teaminfo_build(self, pc) -> dict:
        players = {}

        # get current team count from host
        players["sv_teams"] = self.TeamCount.CurrentValue

        # get all players and their teams and store in a dict
        for pc in unrealsdk.FindAll("WillowPlayerController"):

            # allow only Loader.TheWorld.PersistentLevel.WillowPlayerController
            if pc.Name != "WillowPlayerController":
                continue

            # build dict of players and their teams
            player_name = pc.PlayerReplicationInfo.PlayerName
            team_id = pc.PlayerReplicationInfo.Team.TeamIndex
            
            # player_name "Saint Elmo" will be overriden due to multiclient using same name
            # so, if the name has already been added, append the team_id to the name
            if player_name in players:
                player_name = f"{player_name} ({team_id})"

            players[player_name] = team_id

        unrealsdk.Log(f"Host has built team info: {players} for {pc.PlayerReplicationInfo.PlayerName}")
        self.net_teaminfo_response(players)
        #^ enddef host_teaminfo_build


    # init by client, called on host
    @ServerMethod
    def net_teaminfo_request(self, PC: Optional[unrealsdk.UObject] = None, ) -> None:
        unrealsdk.Log(f"Server received net_teaminfo_request")
        self.host_teaminfo_build(PC)
        #^ enddef net_teaminfo_request


    # init by host, called on client
    @ClientMethod
    def net_teaminfo_response(self, players) -> dict:
        if self.awaiting_menu:
            unrealsdk.Log(f"Client received net_teaminfo_response {players}")
            self.teams_dict = players
            self.build_teams_menu()
            self.update_team_menu()
            self.awaiting_menu = False
            return players
        #^ enddef net_teaminfo_response
    
# endregion netmethod:teaminfo

# create instance
instance = NoCap()

# allow manual loading/unloading
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break

# register mod
ModMenu.RegisterMod(instance)