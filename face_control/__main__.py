"""Entry point — allows `python -m face_control` to start the system ."""

from .controller import FaceController


def main():
    try:
        controller = FaceController()
        controller.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    main()
