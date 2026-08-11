const API_URL = "http://127.0.0.1:8000";

/// ============================================================
// EXAM CONFIGURATION
// ============================================================

// DEVELOPMENT MODE
// 60 seconds = 1 minute.
//
// For the real examination change this to:
// 2 * 60 * 60
//
// which equals 7,200 seconds (2 hours).

const EXAM_DURATION_SECONDS = 2 * 60 * 60;


// Increment this whenever the exam configuration changes.
// This prevents an old localStorage exam from being restored
// with an outdated timer.
const EXAM_VERSION = "v2";


// Storage key for the current exam attempt.
const STORAGE_KEY = "opra_exam_state_v2";

// ============================================================
// STATE
// ============================================================

let questions = [];

let answers = {};

let currentQuestionIndex = 0;

let examStartedAt = null;

let examEndTime = null;

let timerInterval = null;

let examSubmitted = false;


// ============================================================
// DOM
// ============================================================

const loadingElement =
    document.getElementById("loading");

const examElement =
    document.getElementById("exam");

const resultsElement =
    document.getElementById("results");

const reviewElement =
    document.getElementById("review");

const errorElement =
    document.getElementById("error");

const errorMessage =
    document.getElementById("errorMessage");

const timerContainer =
    document.getElementById("timerContainer");

const timerElement =
    document.getElementById("timer");

const questionNumber =
    document.getElementById("questionNumber");

const scoreElement =
    document.getElementById("score");

const progressElement =
    document.getElementById("progress");

const categoryElement =
    document.getElementById("category");

const questionText =
    document.getElementById("questionText");

const optionsElement =
    document.getElementById("options");

const previousButton =
    document.getElementById("previousButton");

const nextButton =
    document.getElementById("nextButton");

const questionNavigator =
    document.getElementById(
        "questionNavigator"
    );

const answeredCountElement =
    document.getElementById(
        "answeredCount"
    );

const unansweredCountElement =
    document.getElementById(
        "unansweredCount"
    );

const submitButton =
    document.getElementById(
        "submitButton"
    );

const finalScoreElement =
    document.getElementById(
        "finalScore"
    );

const percentageElement =
    document.getElementById(
        "percentage"
    );

const resultMessage =
    document.getElementById(
        "resultMessage"
    );

const reviewButton =
    document.getElementById(
        "reviewButton"
    );

const reviewQuestions =
    document.getElementById(
        "reviewQuestions"
    );

const backToResults =
    document.getElementById(
        "backToResults"
    );


// ============================================================
// LOAD QUESTIONS
// ============================================================

async function loadQuestions() {

    try {

        const response =
            await fetch(
                `${API_URL}/questions`
            );


        if (!response.ok) {

            throw new Error(
                `API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        if (
            !data.questions ||
            data.questions.length === 0
        ) {

            throw new Error(
                "No approved questions are available."
            );

        }


        questions =
            data.questions;


        loadingElement.classList.add(
            "hidden"
        );


        /*
            We currently have 8 questions.

            Once the bank contains 120 or more,
            this will use 120 questions.
        */

        if (questions.length > 120) {

            questions =
                shuffleArray(
                    questions
                ).slice(0, 120);

        }


        initialiseExam();


    } catch (error) {

        console.error(error);


        loadingElement.classList.add(
            "hidden"
        );


        errorElement.classList.remove(
            "hidden"
        );


        errorMessage.textContent =
            error.message;

    }

}


// ============================================================
// INITIALISE EXAM
// ============================================================

function initialiseExam() {

    const savedState = loadExamState();


    // ========================================================
    // RESTORE ONLY A COMPATIBLE ACTIVE EXAM
    // ========================================================

    if (
        savedState &&
        savedState.version === EXAM_VERSION &&
        !savedState.submitted &&
        savedState.endTime > Date.now()
    ) {

        answers =
            savedState.answers || {};

        currentQuestionIndex =
            savedState.currentQuestionIndex || 0;

        examStartedAt =
            savedState.startedAt;

        examEndTime =
            savedState.endTime;

        examSubmitted = false;

        startExamInterface();

        startTimer();

        return;
    }

// ============================================================
// START EXAM INTERFACE
// ============================================================

function startExamInterface() {

    resultsElement.classList.add(
        "hidden"
    );

    reviewElement.classList.add(
        "hidden"
    );

    examElement.classList.remove(
        "hidden"
    );

    timerContainer.classList.remove(
        "hidden"
    );


    buildQuestionNavigator();

    showQuestion();

    updateSummary();

}
    // ========================================================
    // START A COMPLETELY NEW EXAM
    // ========================================================

    answers = {};

    currentQuestionIndex = 0;

    examStartedAt =
        Date.now();

    examEndTime =
        examStartedAt +
        EXAM_DURATION_SECONDS * 1000;

    examSubmitted = false;


    saveExamState();

    startExamInterface();

    startTimer();

}


// ============================================================
// QUESTION NAVIGATOR
// ============================================================

function buildQuestionNavigator() {

    questionNavigator.innerHTML = "";


    questions.forEach(
        (question, index) => {

            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "question-number";


            button.textContent =
                index + 1;


            button.addEventListener(
                "click",
                () => {

                    currentQuestionIndex =
                        index;

                    showQuestion();

                    saveExamState();

                }
            );


            questionNavigator.appendChild(
                button
            );

        }
    );


    updateNavigator();

}


// ============================================================
// UPDATE NAVIGATOR
// ============================================================

function updateNavigator() {

    const buttons =
        document.querySelectorAll(
            ".question-number"
        );


    buttons.forEach(
        (button, index) => {

            button.classList.remove(
                "navigator-answered",
                "navigator-current"
            );


            const questionId =
                getQuestionId(
                    questions[index]
                );


            if (
                answers[questionId]
            ) {

                button.classList.add(
                    "navigator-answered"
                );

            }


            if (
                index ===
                currentQuestionIndex
            ) {

                button.classList.add(
                    "navigator-current"
                );

            }

        }
    );

}


// ============================================================
// SHOW QUESTION
// ============================================================

function showQuestion() {

    const question =
        questions[
            currentQuestionIndex
        ];


    if (!question) {
        return;
    }


    const total =
        questions.length;


    const questionId =
        getQuestionId(question);


    questionNumber.textContent =
        `Question ${
            currentQuestionIndex + 1
        } of ${total}`;


    categoryElement.textContent =
        question.topic ||
        question.category ||
        "Pharmacy";


    questionText.textContent =
        question.question || "";


    const progress =
        (
            (currentQuestionIndex + 1) /
            total
        ) * 100;


    progressElement.style.width =
        `${progress}%`;


    optionsElement.innerHTML =
        "";


    const options =
        question.options || {};


    Object.entries(
        options
    ).forEach(
        ([letter, text]) => {

            const button =
                document.createElement(
                    "button"
                );


            button.type =
                "button";


            button.className =
                "option-button";


            if (
                answers[questionId] ===
                letter
            ) {

                button.classList.add(
                    "selected"
                );

            }


            button.innerHTML = `

                <span class="option-letter">
                    ${letter}
                </span>

                <span class="option-text">
                    ${escapeHTML(text)}
                </span>

            `;


            button.addEventListener(
                "click",
                () => selectAnswer(
                    questionId,
                    letter
                )
            );


            optionsElement.appendChild(
                button
            );

        }
    );


    previousButton.disabled =
        currentQuestionIndex === 0;


    if (
        currentQuestionIndex ===
        questions.length - 1
    ) {

        nextButton.textContent =
            "Finish →";

    } else {

        nextButton.textContent =
            "Next →";

    }


    updateNavigator();

    updateSummary();

}


// ============================================================
// ANSWER QUESTION
// ============================================================

function selectAnswer(
    questionId,
    answer
) {

    if (examSubmitted) {
        return;
    }


    answers[questionId] =
        answer;


    saveExamState();


    showQuestion();

}


// ============================================================
// NEXT
// ============================================================

nextButton.addEventListener(
    "click",
    () => {

        if (
            currentQuestionIndex <
            questions.length - 1
        ) {

            currentQuestionIndex++;

            saveExamState();

            showQuestion();

        } else {

            submitExam();

        }

    }
);


// ============================================================
// PREVIOUS
// ============================================================

previousButton.addEventListener(
    "click",
    () => {

        if (
            currentQuestionIndex > 0
        ) {

            currentQuestionIndex--;

            saveExamState();

            showQuestion();

        }

    }
);


// ============================================================
// SUMMARY
// ============================================================

function updateSummary() {

    const answered =
        Object.keys(
            answers
        ).length;


    const unanswered =
        questions.length -
        answered;


    answeredCountElement.textContent =
        answered;


    unansweredCountElement.textContent =
        unanswered;


    scoreElement.textContent =
        `Answered: ${answered}`;


    updateNavigator();

}


// ============================================================
// SUBMIT BUTTON
// ============================================================

submitButton.addEventListener(
    "click",
    submitExam
);


// ============================================================
// SUBMIT EXAM
// ============================================================

function submitExam() {

    if (examSubmitted) {
        return;
    }


    const answered =
        Object.keys(
            answers
        ).length;


    const unanswered =
        questions.length -
        answered;


    let message =
        "Are you sure you want to submit the examination?";


    if (unanswered > 0) {

        message +=
            `\n\nYou have ${unanswered} unanswered question${
                unanswered === 1 ? "" : "s"
            }.`;

    }


    message +=
        "\n\nOnce submitted, you cannot change your answers.";


    const confirmed =
        window.confirm(message);


    if (!confirmed) {
        return;
    }


    finishExam();

}


// ============================================================
// AUTO SUBMIT
// ============================================================

function autoSubmitExam() {

    if (examSubmitted) {
        return;
    }


    alert(
        "Time has expired. Your examination will now be submitted automatically."
    );


    finishExam();

}


// ============================================================
// TIMER
// ============================================================

function startTimer() {

    if (timerInterval) {

        clearInterval(timerInterval);

    }


    const updateTimer = () => {

        const remainingMs =
            Math.max(0, examEndTime - Date.now());


        timerElement.textContent =
            formatTime(remainingMs);


        timerContainer.classList.remove(
            "timer-warning",
            "timer-critical"
        );


        if (remainingMs <= 30000 && remainingMs > 10000) {

            timerContainer.classList.add(
                "timer-warning"
            );

        } else if (remainingMs <= 10000) {

            timerContainer.classList.add(
                "timer-critical"
            );

        }


        if (remainingMs === 0) {

            clearInterval(timerInterval);
            timerInterval = null;
            autoSubmitExam();

        }

    };


    updateTimer();


    timerInterval = setInterval(
        updateTimer,
        1000
    );

}


// ============================================================
// FINISH EXAM
// ============================================================

function finishExam() {

    examSubmitted = true;


    if (timerInterval) {

        clearInterval(
            timerInterval
        );

    }


    timerElement.textContent =
        "00:00:00";


    timerContainer.classList.remove(
        "timer-warning",
        "timer-critical"
    );


    const score =
        calculateScore();


    const total =
        questions.length;


    const percentage =
        Math.round(
            (score / total) * 100
        );


    finalScoreElement.textContent =
        `${score} / ${total}`;


    percentageElement.textContent =
        `${percentage}%`;


    if (percentage >= 80) {

        resultMessage.textContent =
            "Excellent performance. Keep up the good work!";

    } else if (percentage >= 60) {

        resultMessage.textContent =
            "Good effort. Review the questions you missed.";

    } else {

        resultMessage.textContent =
            "Keep practising and review the explanations carefully.";

    }


    examElement.classList.add(
        "hidden"
    );


    resultsElement.classList.remove(
        "hidden"
    );


    timerContainer.classList.add(
        "hidden"
    );


    saveCompletedExam();

}


// ============================================================
// SCORE
// ============================================================

function calculateScore() {

    let score = 0;


    questions.forEach(
        question => {

            const id =
                getQuestionId(
                    question
                );


            if (
                answers[id] ===
                question.correct_answer
            ) {

                score++;

            }

        }
    );


    return score;

}


// ============================================================
// TIME FORMATTING
// ============================================================

function formatTime(milliseconds) {

    const totalSeconds =
        Math.max(0, Math.ceil(milliseconds / 1000));


    const hours =
        Math.floor(totalSeconds / 3600);

    const minutes =
        Math.floor((totalSeconds % 3600) / 60);

    const seconds =
        totalSeconds % 60;


    return [hours, minutes, seconds]
        .map(value => String(value).padStart(2, "0"))
        .join(":");

}


// ============================================================
// REVIEW ANSWERS
// ============================================================

reviewButton.addEventListener(
    "click",
    showReview
);


function showReview() {

    resultsElement.classList.add(
        "hidden"
    );


    reviewElement.classList.remove(
        "hidden"
    );


    reviewQuestions.innerHTML =
        "";


    questions.forEach(
        (question, index) => {

            reviewQuestions.appendChild(
                createReviewCard(
                    question,
                    index
                )
            );

        }
    );

}


function createReviewCard(
    question,
    index
) {

    const card =
        document.createElement(
            "div"
        );


    card.className =
        "review-card";


    const questionId =
        getQuestionId(question);


    const studentAnswer =
        answers[questionId] ||
        null;


    const correctAnswer =
        question.correct_answer;


    const isCorrect =
        studentAnswer ===
        correctAnswer;


    let statusClass;

    let statusText;


    if (!studentAnswer) {

        statusClass =
            "review-unanswered";

        statusText =
            "Unanswered";

    } else if (isCorrect) {

        statusClass =
            "review-correct";

        statusText =
            "Correct";

    } else {

        statusClass =
            "review-incorrect";

        statusText =
            "Incorrect";

    }


    let optionsHTML = "";


    Object.entries(
        question.options || {}
    ).forEach(
        ([letter, text]) => {

            let optionClass =
                "review-option";


            if (
                letter ===
                correctAnswer
            ) {

                optionClass +=
                    " review-correct-option";

            }


            if (
                letter ===
                studentAnswer &&
                letter !==
                correctAnswer
            ) {

                optionClass +=
                    " review-wrong-option";

            }


            optionsHTML += `

                <div
                    class="${optionClass}"
                >

                    <strong>
                        ${letter}.
                    </strong>

                    ${escapeHTML(text)}

                    ${
                        letter === correctAnswer
                            ? " ✓ Correct answer"
                            : ""
                    }

                    ${
                        letter === studentAnswer &&
                        letter !== correctAnswer
                            ? " ✗ Your answer"
                            : ""
                    }

                </div>

            `;

        }
    );


    const explanation =
        (
            question.explanations &&
            question.explanations[
                correctAnswer
            ]
        ) ||
        question.explanation ||
        "No explanation is available.";


    card.innerHTML = `

        <div class="review-card-header">

            <strong>
                Question ${index + 1}
            </strong>

            <span
                class="review-status ${statusClass}"
            >
                ${statusText}
            </span>

        </div>


        <h3>
            ${escapeHTML(
                question.question || ""
            )}
        </h3>


        <div class="review-options">

            ${optionsHTML}

        </div>


        <div class="review-answer-summary">

            <p>
                <strong>
                    Your answer:
                </strong>

                ${
                    studentAnswer ||
                    "Not answered"
                }
            </p>


            <p>
                <strong>
                    Correct answer:
                </strong>

                ${correctAnswer}
            </p>

        </div>


        <div class="review-explanation">

            <strong>
                Explanation
            </strong>

            <p>
                ${escapeHTML(
                    explanation
                )}
            </p>

        </div>

    `;


    return card;

}


// ============================================================
// BACK TO RESULTS
// ============================================================

backToResults.addEventListener(
    "click",
    () => {

        reviewElement.classList.add(
            "hidden"
        );

        resultsElement.classList.remove(
            "hidden"
        );

    }
);


// ============================================================
// PERSIST EXAM STATE
// ============================================================

function saveExamState() {

    if (examSubmitted) {
        return;
    }


    const state = {

        version:
            EXAM_VERSION,

        startedAt:
            examStartedAt,

        endTime:
            examEndTime,

        currentQuestionIndex:
            currentQuestionIndex,

        answers:
            answers,

        submitted:
            false
    };


    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(state)
    );

}

// ============================================================
// LOAD SAVED STATE
// ============================================================

function loadExamState() {

    try {

        const saved =
            localStorage.getItem(
                STORAGE_KEY
            );


        if (!saved) {
            return null;
        }


        return JSON.parse(
            saved
        );

    } catch (error) {

        console.error(
            "Unable to restore exam:",
            error
        );


        return null;

    }

}


// ============================================================
// SAVE COMPLETED EXAM
// ============================================================

function saveCompletedExam() {

    const completedState = {

        version:
            EXAM_VERSION,

        startedAt:
            examStartedAt,

        completedAt:
            Date.now(),

        answers:
            answers,

        score:
            calculateScore(),

        total:
            questions.length,

        submitted:
            true
    };


    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(
            completedState
        )
    );

}


// ============================================================
// QUESTION ID
// ============================================================

function getQuestionId(question) {

    /*
        source_id is the permanent identifier
        coming from the backend.

        Fallback to the array index only if
        source_id doesn't exist.
    */

    return String(
        question.source_id ??
        questions.indexOf(question)
    );

}


// ============================================================
// SHUFFLE
// ============================================================

function shuffleArray(array) {

    const copy =
        [...array];


    for (
        let i = copy.length - 1;
        i > 0;
        i--
    ) {

        const j =
            Math.floor(
                Math.random() *
                (i + 1)
            );


        [
            copy[i],
            copy[j]
        ] =
        [
            copy[j],
            copy[i]
        ];

    }


    return copy;

}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHTML(value) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(
            value ?? ""
        );


    return div.innerHTML;

}


// ============================================================
// START
// ============================================================

loadQuestions();