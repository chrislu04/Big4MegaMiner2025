class_name RedMerc
extends AnimatedSprite2D


func _ready() -> void:
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
	
	frame_changed.connect(_on_frame_changed)
	
func move(direction : Vector2):
	
	match direction.normalized():
		Vector2(-1,0):
			flip_h = false
		Vector2(1,0):
			flip_h = true
	
	play("walk")

func attack(_direction : Vector2):
	
	play("attack")

func idle():
	play("default")

func _on_frame_changed() -> void:
	scale = Vector2(32 / sprite_frames.get_frame_texture(animation,frame).get_size().x, 
		32 / sprite_frames.get_frame_texture(animation,frame).get_size().y)
