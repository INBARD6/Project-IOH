# אנחנו מייבאים את המשחק המלא!
from ufc_fight_simulator_pygame import App

def main():
    try:
        print("Starting FULL UFC Graphic Simulator...")
        game = App()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()