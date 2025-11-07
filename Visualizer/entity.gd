class_name RedMerc
extends AnimatedSprite2D


func _ready() -> void:
	flip_h = true
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
	
func move(direction : Vector2):
	play("walk")

func attack(direction : Vector2):
	play("attack")

func _on_frame_changed() -> void:
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
