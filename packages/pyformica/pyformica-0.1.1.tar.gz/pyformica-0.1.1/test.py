def a():
    a = 1 / 0


try:
    a()
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback

    traceback.print_exc()
