
students = {}

while True:
    print("\nOptions: add / update / print / exit")
    action = input("Enter your choice: ")

    if action == "add":
        name = input("Enter student name to add: ")
        grade = input("Enter grade: ")
        students[name] = grade
        print(f"{name} added with grade {grade}.")

    elif action == "update":
        name = input("Enter student name to update: ")
        if name in students:
            grade = input("Enter new grade: ")
            students[name] = grade
            print(f"{name}'s grade updated to {grade}.")
        else:
            print(f"{name} not found in records.")

    elif action == "print":
        if len(students) == 0:
            print("No students available.")
        else:
            print("\n--- All Student Grades ---")
            for name, grade in students.items():
                print(name, ":", grade)

    elif action == "exit":
        print("")
        break

    else:
        print("Invalid option. Please choose add, update, print, or exit.")
