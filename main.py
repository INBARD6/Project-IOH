"""
main.py
נקודת כניסה ראשית לאפליקציית UFC Management System
"""

from MainController import MainController


def main():
    """
    פונקציה ראשית - מפעילה את הבקר הראשי
    """
    try:
        controller = MainController()
        controller.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  program stopped by user.")
    except Exception as e:
        print(f"\n❌ critical error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()