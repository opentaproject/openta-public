# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from exercises.models import Exercise, Question, Answer
from django.contrib.auth.models import User

# Convenience function for writing array of rows to CSV file
def write_csv(filename, data):
    with open(filename, "w") as out_file:
        for row in data:
            out_file.write("\t".join(map(str, row)))
            out_file.write("\n")


# Get all published exercises
exercises = Exercise.objects.filter(meta__published=True)

exercise_attempts = []
for exercise in exercises:
    n_answers = Answer.objects.filter(question__exercise=exercise, user__groups__name="Student").count()
    exercise_attempts.append((exercise.pk, exercise.name.strip(), n_answers))

write_csv("exercise_num_attempts.txt", exercise_attempts)

# Get all active students
students = User.objects.filter(groups__name="Student", is_active=True)

exercise_num_correct = []

# Loop through exercises
for exercise in exercises:
    # Get all questions for this exercise
    questions = Question.objects.filter(exercise=exercise)
    # Want to count the intersection of all students that have answered correctly on all questions
    correct_per_question = []
    if questions.count() > 0:
        for question in questions:
            # Get all students that have answered this question correctly
            correct = (
                students.filter(answer__question=question, answer__correct=True).values_list("pk", flat=True).distinct()
            )
            correct_per_question.append(set(correct))

        all_correct = set.intersection(*correct_per_question)
        n_correct = len(all_correct)
        exercise_num_correct.append((exercise.pk, exercise.name.strip(), n_correct))

write_csv("exercise_num_correct.txt", exercise_num_correct)
