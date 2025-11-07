extends Node

var backend_path : String = "main.py"
var AI_folder : String = "AI Agents"

var default_map : String = "C:/Users/kenji/OneDrive/Desktop/GitHub_Projects/MegaMiner2025/maps/test_map.json"

var AI_agent1_file_path : String = ""
var AI_agent2_file_path : String = ""

# So depending on the system, the path provided will have '\' which doesn't work on every system, so this function just changes '\' to '/' so that it does
func convert_string_to_readable(string : String) -> String:
	var new_string : String = string.replace('\\', '/')
	
	return new_string
