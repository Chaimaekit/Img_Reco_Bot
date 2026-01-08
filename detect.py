import pyautogui
import time
import re



def get_final_placements():
    print("Move your mouse to the target and wait...")
    time.sleep(3)
    current_pos = pyautogui.position()
    print("Position is captured !!")
    return current_pos


def given_position(current_pos, target_pos):

    right = get_final_placements()
    left = get_final_placements()
    up = get_final_placements()
    down = get_final_placements()

    current_pos_X = re.sub("[() ]", "", str(current_pos)).split(",")[0]
    current_pos_Y = re.sub("[() ]", "", str(current_pos)).split(",")[1]
    target_pos_X = re.sub("[() ]", "", str(target_pos)).split(",")[0]
    target_pos_Y = re.sub("[() ]", "", str(target_pos)).split(",")[1]
    while current_pos_X != target_pos_X or current_pos_Y != target_pos_Y:
        if current_pos_X < target_pos_X:
            pyautogui.moveTo(right)
            current_pos_X = current_pos_X + 1
        elif current_pos_X > target_pos_X:
            pyautogui.moveTo(left)
            current_pos_X = current_pos_X - 1
        if current_pos_Y < target_pos_Y:
            pyautogui.moveTo(down)
            current_pos_Y = current_pos_Y + 1
        elif current_pos_Y > target_pos_Y:
            pyautogui.moveTo(up)
            current_pos_Y = current_pos_Y - 1
    print("Reached the target position!")


if __name__ == "__main__":
    current_position = input("Enter the current position...")
    target_position = input("Enter the target position...")
    given_position(current_position, target_position)