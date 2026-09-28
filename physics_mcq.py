import random
import os
import sys

# ============================================================
# PHYSICS FORMULA MCQ QUIZ
# VECTORS + KINEMATICS + NEWTON'S LAWS OF MOTION
# ============================================================

questions = [

# ========================= VECTORS =========================

{
    "q": "The magnitude of vector A = 3i + 4j is:",
    "options": ["5", "7", "1", "25"],
    "answer": "5"
},
{
    "q": "If Ax = A cos(theta) and Ay = A sin(theta), theta is measured from:",
    "options": ["Positive x-axis", "Positive y-axis", "Negative x-axis", "Negative y-axis"],
    "answer": "Positive x-axis"
},
{
    "q": "The unit vector in the direction of vector A is:",
    "options": ["A/|A|", "|A|/A", "A²", "1/A"],
    "answer": "A/|A|"
},
{
    "q": "The resultant of two vectors A and B inclined at angle theta is:",
    "options": [
        "sqrt(A²+B²+2AB cos(theta))",
        "sqrt(A²+B²-2AB cos(theta))",
        "A+B cos(theta)",
        "AB sin(theta)"
    ],
    "answer": "sqrt(A²+B²+2AB cos(theta))"
},
{
    "q": "The minimum possible magnitude of the resultant of vectors A and B is:",
    "options": ["|A-B|", "A+B", "AB", "sqrt(A²+B²)"],
    "answer": "|A-B|"
},
{
    "q": "The maximum possible magnitude of the resultant of vectors A and B is:",
    "options": ["A+B", "|A-B|", "AB", "A/B"],
    "answer": "A+B"
},
{
    "q": "If two vectors are perpendicular, their resultant magnitude is:",
    "options": [
        "sqrt(A²+B²)",
        "A+B",
        "|A-B|",
        "AB"
    ],
    "answer": "sqrt(A²+B²)"
},
{
    "q": "The dot product of two vectors A and B is:",
    "options": ["AB cos(theta)", "AB sin(theta)", "A+B", "A×B"],
    "answer": "AB cos(theta)"
},
{
    "q": "If A dot B = 0, then the two non-zero vectors are:",
    "options": ["Perpendicular", "Parallel", "Anti-parallel", "Equal"],
    "answer": "Perpendicular"
},
{
    "q": "The cross product magnitude of A and B is:",
    "options": ["AB sin(theta)", "AB cos(theta)", "A+B", "|A-B|"],
    "answer": "AB sin(theta)"
},
{
    "q": "The area of the parallelogram formed by vectors A and B is:",
    "options": ["|A × B|", "A · B", "A+B", "AB cos(theta)"],
    "answer": "|A × B|"
},
{
    "q": "The area of the triangle formed by vectors A and B is:",
    "options": ["1/2 |A × B|", "|A × B|", "A · B", "2|A × B|"],
    "answer": "1/2 |A × B|"
},
{
    "q": "Which relation is correct?",
    "options": [
        "i × j = k",
        "i × j = -k",
        "i · j = 1",
        "j × k = -i"
    ],
    "answer": "i × j = k"
},
{
    "q": "The value of i · i is:",
    "options": ["1", "0", "-1", "i"],
    "answer": "1"
},
{
    "q": "The value of i × i is:",
    "options": ["0", "1", "-1", "i"],
    "answer": "0"
},

# ========================= KINEMATICS =========================

{
    "q": "Instantaneous velocity is defined as:",
    "options": [
        "dr/dt",
        "dx/dt²",
        "dv/dt",
        "ds/dt²"
    ],
    "answer": "dr/dt"
},
{
    "q": "Instantaneous acceleration is:",
    "options": [
        "dv/dt",
        "dx/dt",
        "dr/dt",
        "v/t"
    ],
    "answer": "dv/dt"
},
{
    "q": "Which relation connects acceleration, velocity and position?",
    "options": [
        "a = v dv/dx",
        "a = dx/dv",
        "a = v dx/dt",
        "a = x dv/dt"
    ],
    "answer": "a = v dv/dx"
},
{
    "q": "The first equation of uniformly accelerated motion is:",
    "options": [
        "v = u + at",
        "s = ut + 1/2 at²",
        "v² = u² + 2as",
        "s = vt"
    ],
    "answer": "v = u + at"
},
{
    "q": "The second equation of uniformly accelerated motion is:",
    "options": [
        "s = ut + 1/2 at²",
        "v = u + at",
        "v² = u² + 2as",
        "a = v/t"
    ],
    "answer": "s = ut + 1/2 at²"
},
{
    "q": "Which equation does NOT contain time explicitly?",
    "options": [
        "v² = u² + 2as",
        "v = u + at",
        "s = ut + 1/2at²",
        "s = (u+v)t/2"
    ],
    "answer": "v² = u² + 2as"
},
{
    "q": "Displacement in the nth second is:",
    "options": [
        "u + a/2(2n-1)",
        "un + 1/2an²",
        "u + an",
        "un - 1/2an²"
    ],
    "answer": "u + a/2(2n-1)"
},
{
    "q": "For constant acceleration, average velocity is:",
    "options": [
        "(u+v)/2",
        "u+v",
        "uv/2",
        "v-u"
    ],
    "answer": "(u+v)/2"
},
{
    "q": "The slope of a position-time graph gives:",
    "options": ["Velocity", "Acceleration", "Displacement", "Speed²"],
    "answer": "Velocity"
},
{
    "q": "The slope of a velocity-time graph gives:",
    "options": ["Acceleration", "Velocity", "Displacement", "Distance"],
    "answer": "Acceleration"
},
{
    "q": "The area under a velocity-time graph gives:",
    "options": ["Displacement", "Acceleration", "Velocity", "Jerk"],
    "answer": "Displacement"
},
{
    "q": "The area under an acceleration-time graph gives:",
    "options": ["Change in velocity", "Displacement", "Distance", "Acceleration"],
    "answer": "Change in velocity"
},
{
    "q": "Relative velocity of A with respect to B is:",
    "options": [
        "vA - vB",
        "vA + vB always",
        "vA × vB",
        "vB - vA always"
    ],
    "answer": "vA - vB"
},
{
    "q": "If two objects move in opposite directions with speeds v1 and v2, their relative speed is:",
    "options": ["v1+v2", "|v1-v2|", "v1v2", "v1/v2"],
    "answer": "v1+v2"
},

# ========================= VERTICAL MOTION =========================

{
    "q": "For a freely falling object starting from rest, its velocity after time t is:",
    "options": ["gt", "g/t", "1/2gt²", "2gt"],
    "answer": "gt"
},
{
    "q": "Distance travelled by a freely falling object from rest in time t is:",
    "options": ["1/2gt²", "gt", "2gt²", "g/t²"],
    "answer": "1/2gt²"
},
{
    "q": "For an object thrown vertically upward, its velocity after time t is:",
    "options": ["u-gt", "u+gt", "gt-u", "u+1/2gt²"],
    "answer": "u-gt"
},
{
    "q": "Maximum height reached by a body projected vertically upward with speed u is:",
    "options": ["u²/(2g)", "u²/g", "2u²/g", "ug/2"],
    "answer": "u²/(2g)"
},
{
    "q": "Time taken to reach maximum height for a vertically projected body is:",
    "options": ["u/g", "2u/g", "u/2g", "g/u"],
    "answer": "u/g"
},
{
    "q": "Total time of flight for a body projected vertically upward and returning to the same level is:",
    "options": ["2u/g", "u/g", "u²/g", "2g/u"],
    "answer": "2u/g"
},

# ========================= PROJECTILE =========================

{
    "q": "Horizontal component of projectile velocity u at angle theta is:",
    "options": ["u cos(theta)", "u sin(theta)", "u tan(theta)", "u/cos(theta)"],
    "answer": "u cos(theta)"
},
{
    "q": "Vertical component of projectile velocity u at angle theta is:",
    "options": ["u sin(theta)", "u cos(theta)", "u tan(theta)", "u/sin(theta)"],
    "answer": "u sin(theta)"
},
{
    "q": "Horizontal acceleration of an ideal projectile is:",
    "options": ["0", "g", "-g", "u"],
    "answer": "0"
},
{
    "q": "Vertical acceleration of a projectile, taking upward as positive, is:",
    "options": ["-g", "0", "g", "u"],
    "answer": "-g"
},
{
    "q": "Time of flight of a projectile returning to the same level is:",
    "options": [
        "2u sin(theta)/g",
        "u sin(theta)/g",
        "u cos(theta)/g",
        "u² sin(theta)/g"
    ],
    "answer": "2u sin(theta)/g"
},
{
    "q": "Maximum height of a projectile is:",
    "options": [
        "u²sin²(theta)/(2g)",
        "u²sin(theta)/(2g)",
        "u²cos²(theta)/(2g)",
        "u²/g"
    ],
    "answer": "u²sin²(theta)/(2g)"
},
{
    "q": "Horizontal range of a projectile returning to the same level is:",
    "options": [
        "u²sin(2theta)/g",
        "u²sin(theta)/g",
        "2u²sin(theta)/g",
        "u²cos(theta)/g"
    ],
    "answer": "u²sin(2theta)/g"
},
{
    "q": "The angle of projection for maximum horizontal range is:",
    "options": ["45°", "30°", "60°", "90°"],
    "answer": "45°"
},
{
    "q": "Maximum range of a projectile is:",
    "options": ["u²/g", "u²/2g", "2u²/g", "u/g"],
    "answer": "u²/g"
},
{
    "q": "The trajectory of an ideal projectile is:",
    "options": ["Parabola", "Circle", "Straight line", "Ellipse"],
    "answer": "Parabola"
},
{
    "q": "The equation of trajectory of a projectile is:",
    "options": [
        "y = x tan(theta) - gx²/(2u²cos²(theta))",
        "y = x sin(theta)",
        "y = ut + 1/2gt²",
        "y = x² tan(theta)"
    ],
    "answer": "y = x tan(theta) - gx²/(2u²cos²(theta))"
},
{
    "q": "At the highest point of projectile motion, its vertical velocity is:",
    "options": ["0", "u", "g", "u sin(theta)"],
    "answer": "0"
},
{
    "q": "At the highest point, the speed of a projectile is:",
    "options": ["u cos(theta)", "u sin(theta)", "u", "0"],
    "answer": "u cos(theta)"
},
{
    "q": "For a projectile returning to the same height, horizontal distance at maximum height is:",
    "options": ["R/2", "R", "2R", "R/4"],
    "answer": "R/2"
},
{
    "q": "For a projectile, the relation between range R and maximum height H is:",
    "options": [
        "R = 4H cot(theta)",
        "R = H cot(theta)",
        "R = 2H tan(theta)",
        "R = 4H tan(theta)"
    ],
    "answer": "R = 4H cot(theta)"
},

# ========================= NLM =========================

{
    "q": "Newton's second law in general form is:",
    "options": [
        "F = dp/dt",
        "F = mv",
        "F = ma²",
        "F = p/t²"
    ],
    "answer": "F = dp/dt"
},
{
    "q": "For constant mass, Newton's second law becomes:",
    "options": ["F = ma", "F = mv", "F = m/a", "F = a/m"],
    "answer": "F = ma"
},
{
    "q": "Linear momentum is:",
    "options": ["p = mv", "p = ma", "p = m/v", "p = F/t"],
    "answer": "p = mv"
},
{
    "q": "Impulse is equal to:",
    "options": ["Change in momentum", "Change in position", "Change in acceleration", "Force/time"],
    "answer": "Change in momentum"
},
{
    "q": "For a constant force F acting for time t, impulse is:",
    "options": ["Ft", "F/t", "F+t", "F/t²"],
    "answer": "Ft"
},
{
    "q": "The weight of a body of mass m is:",
    "options": ["mg", "m/g", "g/m", "m+g"],
    "answer": "mg"
},
{
    "q": "Newton's third law states:",
    "options": [
        "FAB = -FBA",
        "FAB = FBA in same direction",
        "F = ma",
        "Net force is always zero"
    ],
    "answer": "FAB = -FBA"
},
{
    "q": "Action and reaction forces act on:",
    "options": [
        "Different bodies",
        "The same body",
        "Only stationary bodies",
        "Only moving bodies"
    ],
    "answer": "Different bodies"
},

# ========================= FRICTION =========================

{
    "q": "Static friction satisfies:",
    "options": [
        "fs ≤ μsN",
        "fs = μsN always",
        "fs > μsN",
        "fs = μkN always"
    ],
    "answer": "fs ≤ μsN"
},
{
    "q": "Maximum static friction is:",
    "options": ["μsN", "μkN", "N/μs", "μs/N"],
    "answer": "μsN"
},
{
    "q": "Kinetic friction is:",
    "options": ["μkN", "μsN always", "mg", "ma"],
    "answer": "μkN"
},
{
    "q": "Generally, the coefficient relation is:",
    "options": ["μs ≥ μk", "μs < μk", "μs = 0", "μk = 0 always"],
    "answer": "μs ≥ μk"
},
{
    "q": "The angle of friction phi satisfies:",
    "options": ["tan(phi) = μ", "sin(phi)=μ", "cos(phi)=μ", "tan(phi)=1/μ"],
    "answer": "tan(phi) = μ"
},
{
    "q": "The angle of repose theta satisfies:",
    "options": ["tan(theta)=μs", "sin(theta)=μs", "cos(theta)=μs", "tan(theta)=1/μs"],
    "answer": "tan(theta)=μs"
},

# ========================= INCLINED PLANE =========================

{
    "q": "For a block on an incline theta, component of weight parallel to plane is:",
    "options": ["mg sin(theta)", "mg cos(theta)", "mg tan(theta)", "mg"],
    "answer": "mg sin(theta)"
},
{
    "q": "Component of weight perpendicular to an inclined plane is:",
    "options": ["mg cos(theta)", "mg sin(theta)", "mg tan(theta)", "0"],
    "answer": "mg cos(theta)"
},
{
    "q": "Normal reaction on a block on a frictionless incline is:",
    "options": ["mg cos(theta)", "mg sin(theta)", "mg", "0"],
    "answer": "mg cos(theta)"
},
{
    "q": "Acceleration of a block sliding down a frictionless incline is:",
    "options": ["g sin(theta)", "g cos(theta)", "g tan(theta)", "g"],
    "answer": "g sin(theta)"
},
{
    "q": "Acceleration of a block sliding down a rough incline with coefficient mu is:",
    "options": [
        "g(sin(theta)-mu cos(theta))",
        "g(sin(theta)+mu cos(theta))",
        "g cos(theta)",
        "mu g sin(theta)"
    ],
    "answer": "g(sin(theta)-mu cos(theta))"
},
{
    "q": "For a block sliding upward on a rough incline, the retardation magnitude is:",
    "options": [
        "g(sin(theta)+mu cos(theta))",
        "g(sin(theta)-mu cos(theta))",
        "g cos(theta)",
        "mu g"
    ],
    "answer": "g(sin(theta)+mu cos(theta))"
},

# ========================= ELEVATOR =========================

{
    "q": "For an elevator accelerating upward with acceleration a, apparent weight is:",
    "options": ["m(g+a)", "m(g-a)", "mg", "ma"],
    "answer": "m(g+a)"
},
{
    "q": "For an elevator accelerating downward with acceleration a, apparent weight is:",
    "options": ["m(g-a)", "m(g+a)", "mg", "ma"],
    "answer": "m(g-a)"
},
{
    "q": "In free fall, the apparent weight of a person is:",
    "options": ["0", "mg", "ma", "2mg"],
    "answer": "0"
},

# ========================= PSEUDO FORCE =========================

{
    "q": "Pseudo force in a frame accelerating with a0 is:",
    "options": ["-ma0", "ma0", "mg", "m/a0"],
    "answer": "-ma0"
},
{
    "q": "Pseudo force acts in which direction relative to the acceleration of the frame?",
    "options": [
        "Opposite",
        "Same",
        "Perpendicular",
        "Random"
    ],
    "answer": "Opposite"
},
{
    "q": "Effective gravity in an accelerating frame is:",
    "options": [
        "g_eff = g - a_frame",
        "g_eff = g + a_frame always",
        "g_eff = g/a_frame",
        "g_eff = ga_frame"
    ],
    "answer": "g_eff = g - a_frame"
},

# ========================= PULLEY =========================

{
    "q": "For an ideal massless string passing over a frictionless pulley, tension is:",
    "options": [
        "Same throughout the string",
        "Zero everywhere",
        "Different everywhere",
        "Equal to mg always"
    ],
    "answer": "Same throughout the string"
},
{
    "q": "For an Atwood machine with masses m1 and m2, acceleration magnitude is:",
    "options": [
        "|m2-m1|g/(m1+m2)",
        "(m1+m2)g",
        "m1m2g",
        "|m2-m1|g"
    ],
    "answer": "|m2-m1|g/(m1+m2)"
},
{
    "q": "For an ideal Atwood machine, tension is:",
    "options": [
        "2m1m2g/(m1+m2)",
        "(m1+m2)g",
        "m1m2g",
        "m1g-m2g"
    ],
    "answer": "2m1m2g/(m1+m2)"
},
{
    "q": "For an inextensible string, its total length remains:",
    "options": ["Constant", "Zero", "Increasing", "Decreasing"],
    "answer": "Constant"
},
{
    "q": "For a system with total external force F and total mass M, acceleration is:",
    "options": ["F/M", "FM", "M/F", "F+M"],
    "answer": "F/M"
}

]

# ============================================================
# QUIZ ENGINE
# ============================================================

rng = random.SystemRandom()


def clear_screen():
    os.system("clear" if os.name != "nt" else "cls")


def ask_question(number, total, question):
    print("\n" + "=" * 65)
    print(f"QUESTION {number}/{total}")
    print("=" * 65)
    print(question["q"])
    print()

    # Shuffle options independently every time
    options = question["options"].copy()
    rng.shuffle(options)

    letters = ["A", "B", "C", "D"]

    for letter, option in zip(letters, options):
        print(f"  {letter}) {option}")

    while True:
        answer = input("\nYour answer (A/B/C/D): ").strip().upper()

        if answer in letters:
            break

        print("Please enter A, B, C or D.")

    chosen = options[letters.index(answer)]

    if chosen == question["answer"]:
        print("\n✅ CORRECT!")
        return True
    else:
        print("\n❌ WRONG!")
        print(f"Correct answer: {question['answer']}")
        return False


def run_quiz():
    clear_screen()

    print("=" * 65)
    print("        ⚡ PHYSICS FORMULA MCQ CHALLENGE ⚡")
    print("=" * 65)
    print()
    print("Topics:")
    print("  • Vectors")
    print("  • Kinematics")
    print("  • Projectile Motion")
    print("  • Newton's Laws of Motion")
    print("  • Friction")
    print("  • Inclined Planes")
    print("  • Elevator")
    print("  • Pseudo Force")
    print("  • Pulley Systems")
    print()
    print("Questions and options are RANDOMIZED every time.")
    print()

    input("Press ENTER to start...")

    # Fresh random question order every game
    quiz = questions.copy()
    rng.shuffle(quiz)

    # Ask all questions
    score = 0

    for i, question in enumerate(quiz, 1):
        if ask_question(i, len(quiz), question):
            score += 1

    percentage = (score / len(quiz)) * 100

    print("\n" + "=" * 65)
    print("                    QUIZ COMPLETE")
    print("=" * 65)

    print(f"\nScore      : {score}/{len(quiz)}")
    print(f"Percentage : {percentage:.1f}%")

    if percentage >= 90:
        print("🔥 Excellent formula command!")
    elif percentage >= 75:
        print("💪 Very good! Keep practicing.")
    elif percentage >= 60:
        print("📚 Good start. Revise the formulas you missed.")
    else:
        print("🧠 Time for another revision round!")

    print("\n")


def main():
    while True:
        run_quiz()

        again = input("Play another randomized quiz? (Y/N): ").strip().upper()

        if again != "Y":
            print("\nGood luck with your test! 🚀")
            break

        clear_screen()


if __name__ == "__main__":
    main()

