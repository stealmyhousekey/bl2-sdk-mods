import unrealsdk
from typing import Dict, Optional, Any, cast
from Mods.ModMenu import (
	Mods,
	EnabledSaveType,
	Game,
	Keybind,
	KeybindManager,
	ModTypes,
	Options,
	SDKMod,
	Hook,
	RegisterMod,
	ClientMethod,
	ServerMethod
)
from Mods.Enums import ENetMode, EModifierType

def get_pc() -> unrealsdk.UObject:
	return unrealsdk.GetEngine().GamePlayers[0].Actor

def is_host():
    return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == ENetMode.NM_ListenServer

def is_client():
	return unrealsdk.GetEngine().GetCurrentWorldInfo().NetMode == ENetMode.NM_Client

def log(mod: SDKMod, *args: Any) -> None:
    if mod.EnableLogging.CurrentValue:
        unrealsdk.Log(f"[{mod.Name}]", *args)
          
# same as log, but prefix with player class
def logc(mod: SDKMod, pc: unrealsdk.UObject, *args: Any) -> None:
    if mod.EnableLogging.CurrentValue:
        unrealsdk.Log(f"[{mod.Name}] {get_vaulthunter_class(pc)}", *args)
          
# same as log, but ignores logging settings
def logf(mod: SDKMod, *args: Any) -> None:
    unrealsdk.Log(f"[{mod.Name}]", *args)

def get_vaulthunter_class(PC: Optional[unrealsdk.UObject] = None) -> str:
    if PC is None:
        PC = get_pc()
    return str(PC.PlayerClass.CharacterNameId.CharacterClassId.ClassName)


def get_player_controller():
    """
    Get the current WillowPlayerController Object.
    :return: WillowPlayerController
    """
    return unrealsdk.GetEngine().GamePlayers[0].Actor


def get_obj_path_name(uobject: unrealsdk.UObject):
    """
    Get the full correct name of the provided object.
    :param uobject: UObject
    :return: String of the Path Name
    """
    if uobject:
        return uobject.PathName(uobject)
    else:
        return "None"


def console_command(command: str, write_to_log: bool = False):
    """
    Executes a normal console command
    :param command: String, the command to execute.
    :param write_to_log: Bool, write to Log
    :return: None
    """
    get_player_controller().ConsoleCommand(command, write_to_log)


def obj_is_in_class(uobject: unrealsdk.UObject, uclass: str):
    """
    Compares the given Objects class with the given class.
    :param uobject: UObject
    :param uclass: String, the Class to compare with
    :return: Bool, whether it's in the Class.
    """
    return bool(uobject.Class == unrealsdk.FindClass(uclass))


def get_weapon_holding():
    """
    Get the weapon the WillowPlayerPawn is currently holding.
    :return: WillowWeapon
    """
    return unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn.Weapon


def get_world_info():
    return unrealsdk.GetEngine().GetCurrentWorldInfo()


def feedback(title: str, text: str, duration: float):
    pc = get_player_controller()
    if pc is not None:
        hud = pc.GetHUDMovie()
        hud.AddTrainingText(text, title, duration, (), "", False, 0, pc.PlayerReplicationInfo, True)
