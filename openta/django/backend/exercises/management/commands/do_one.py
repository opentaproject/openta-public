# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2018-2025 Stellan Östlund and Hampus Linander

from django.core.management.base import BaseCommand, CommandError
from exercises.models import Exercise, Answer, Question, ImageAnswer, AuditExercise
from django.contrib.auth.models import User
from course.models import Course
from django.conf import settings
from users.models import OpenTAUser
import exercises
import aggregation as ag
import logging

from course.models import Course

logger = logging.getLogger(__name__)

BIN_LENGTH = settings.BIN_LENGTH


class Command(BaseCommand):

    help = "reinitialize Aggregations and Bincounts"

    def handle(self, *args, **options):
        exercise_key = "EXAMPLE_EXERICSE_KEY"
        exercise = Exercise.objects.get(exercise_key=exercise_key)
        questions = Question.objects.filter(exercise=exercise)
        for question in questions:
            print("QUESTINO = ", question, question.question_key)
            print("EXERCISE BELONGIN TO QUESTION = ", question.exercise)
        print("QUESTIONS = ", questions.count())
        username = "devcha@student.chalmers.se"
        user = User.objects.get(username=username)
        print("USER = ", user)
        return
        answers = Answer.objects.filter(question=questions, user=user)

        answers = Answer.objects.all().distinct("question__exercise", "user")
        nobjects = answers.count()
        print("NUMBER OF DISTINCT ANSWERS = ", nobjects)
        aggregations = ag.models.Aggregation.objects.all()
        for aggregation in aggregations:
            aggregation.delete()
        imageanswers = ImageAnswer.objects.all().distinct("exercise", "user")
        audits = AuditExercise.objects.all().distinct("exercise", "student")
        ind = 0

        print("THERE ARE ", audits.count(), " AUDITS")
        for audit in audits:
            user = audit.student
            exercise = audit.exercise
            try:
                course = exercise.course
                ct = ag.models.Aggregation.objects.filter(user=user, exercise=exercise).count()
            except:
                print("REINITIALIZE  EXERCISE.COURSE FAILED ", audit)
                ct = 0
            if ct == 0:
                if user.username == "devcha@student.chalmers.se":
                    print("AUDIT USER = ", user, " AND EXERCISE ", exercise)
                gb, created = ag.models.Aggregation.objects.get_or_create(course=course, user=user, exercise=exercise)
                #        print("FAILED IMAGEANSWER ENTRY USER = ", user, "COURS = ", course, "EXERCISE = ", exercise)

        print("THERE ARE ", imageanswers.count(), " IMAGANSWERS")
        for imageanswer in imageanswers:
            user = imageanswer.user
            exercise = imageanswer.exercise
            try:
                course = exercise.course
                ct = ag.models.Aggregation.objects.filter(user=user, exercise=exercise).count()
            except:
                print("REINITIALIZE  EXERCISE.COURSE FAILED ", imageanswer)
                ct = 0
            if ct == 0:
                gb, created = ag.models.Aggregation.objects.get_or_create(course=course, user=user, exercise=exercise)
                #        print("FAILED IMAGEANSWER ENTRY USER = ", user, "COURS = ", course, "EXERCISE = ", exercise)

        logger.info("Start ANALYXING " + str(nobjects) + " Answers")
        interval = int(nobjects / 60)
        for answer in answers:
            if not answer.question:
                print(
                    "ANSWER IS NOT ASSOCIATED WITH A QUESTION ANYMORE",
                    answer.user,
                    answer,
                    answer.date,
                )
        ind = 1
        for answer in answers:
            if answer.question:
                exercise = answer.question.exercise
                question_key = answer.question.question_key
                user = answer.user
                course = exercise.course
                gb, created = ag.models.Aggregation.objects.update_or_create(
                    course=course, user=user, exercise=exercise
                )
            else:
                print("DANGLING QUESTION FOUND", answer.user, answer, answer.date)
            if (ind % interval) == 0:
                print("X", end="", flush=True)
            ind += 1

        print("REINITIALIZED aggregation.models.Aggregation")
        # for aggregation in aggregations:
        #    attempts += aggregation.attempt_count
        #    print("aggregation = ", aggregation, aggregation.attempt_count)

        # logger.info('Started aggregation.models.Exercises')
        # for bincount in bincounts:
        #    bincount.delete()
        # courses = Course.objects.all()
        # tot = 0
        # for course in courses:
        #    answers = Answer.objects.filter(question__exercise__course=course)
        #    for answer in answers:
        #        tot += 1
        #        exercise = answer.question.exercise
        #        user = answer.user
        #        date = answer.date
        #        # print("answer = ", answer )
        #        bin = int(date.timestamp() / BIN_LENGTH)  # BIN EVERY 5 MINUTES
        #        bincounts, _ = ag.models.Exercises.objects.get_or_create(
        #            course=course, exercise=exercise, bin=bin
        #        )
        #        # print("DATE: bin = ", bin , " DATE = ", date , bincounts.bin , bincounts.count )
        #        bincounts.count += 1
        #        bincounts.save()
        # bins = ag.models.Exercises.objects.all().count()
        # print("TOTAL ATTMEMPTS = ", attempts)
        # print("TOTAL ANSWERS = ", tot, " IN ", bins, " BINS ")
