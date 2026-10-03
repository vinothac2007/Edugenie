const form = document.getElementById("edugenie-form");
const taskSelect = document.getElementById("task");
const input = document.getElementById("user-input");
const levelContainer = document.getElementById("level-container");
const levelSelect = document.getElementById("level");

const submitButton = document.getElementById("submit-button");
const buttonText = document.getElementById("button-text");
const loadingSpinner = document.getElementById("loading-spinner");

const resultSection = document.getElementById("result-section");
const resultContainer = document.getElementById("result");
const copyButton = document.getElementById("copy-button");

const taskPlaceholders = {
    qa: "Example: What is the largest ocean in the world?",
    explain: "Example: Explain the Pythagoras theorem in simple terms.",
    quiz: "Enter a topic or passage to generate a 3-question quiz.",
    summarize: "Paste the educational passage you want to summarize.",
    learn: "Example: I want to learn SQL from beginner to advanced."
};

const buttonLabels = {
    qa: "Get Answer",
    explain: "Explain Topic",
    quiz: "Generate Quiz",
    summarize: "Summarize",
    learn: "Create Learning Path"
};

function updateTaskUI() {
    const task = taskSelect.value;

    input.placeholder =
        taskPlaceholders[task] || "Enter your text here...";

    buttonText.textContent =
        buttonLabels[task] || "Submit";

    if (task === "learn") {
        levelContainer.classList.remove("hidden");
    } else {
        levelContainer.classList.add("hidden");
    }
}

function setLoading(isLoading) {
    submitButton.disabled = isLoading;

    if (isLoading) {
        buttonText.textContent = "Thinking...";
        loadingSpinner.classList.remove("hidden");
    } else {
        loadingSpinner.classList.add("hidden");

        buttonText.textContent =
            buttonLabels[taskSelect.value] || "Submit";
    }
}

function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
}

function renderTextResult(text) {
    resultContainer.innerHTML = `
        <div class="text-result">
            ${escapeHtml(text)}
        </div>
    `;
}

function renderQuiz(questions) {
    if (!Array.isArray(questions) || questions.length === 0) {
        resultContainer.innerHTML = `
            <div class="error">
                Unable to display the quiz.
            </div>
        `;
        return;
    }

    resultContainer.innerHTML = questions
        .map((question, index) => {

            const options =
                Array.isArray(question.options)
                    ? question.options
                    : [];

            const optionsHtml = options
                .map((option, optionIndex) => {

                    const letter =
                        String.fromCharCode(65 + optionIndex);

                    return `
                        <div class="quiz-option">
                            <strong>${letter}.</strong>
                            ${escapeHtml(option)}
                        </div>
                    `;
                })
                .join("");

            const explanation =
                question.explanation
                    ? `
                        <br>
                        <strong>Explanation:</strong>
                        ${escapeHtml(question.explanation)}
                    `
                    : "";

            return `
                <div class="quiz-question">

                    <h3>
                        ${index + 1}.
                        ${escapeHtml(question.question)}
                    </h3>

                    ${optionsHtml}

                    <div class="quiz-answer">

                        <strong>
                            Correct answer:
                        </strong>

                        ${escapeHtml(question.correct_answer)}

                        ${explanation}

                    </div>

                </div>
            `;
        })
        .join("");
}

async function callApi(url, data) {

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    });

    let result;

    try {
        result = await response.json();
    } catch (error) {
        throw new Error(
            "The server returned an invalid response."
        );
    }

    if (!response.ok) {
        throw new Error(
            result.detail ||
            "Something went wrong on the server."
        );
    }

    return result;
}

form.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();

        const task = taskSelect.value;
        const text = input.value.trim();

        if (!text) {

            resultSection.classList.remove("hidden");

            resultContainer.innerHTML = `
                <div class="error">
                    Please enter some text first.
                </div>
            `;

            return;
        }

        setLoading(true);

        resultSection.classList.remove("hidden");

        resultContainer.innerHTML = `
            <p>
                EduGenie is processing your request...
            </p>
        `;

        try {

            let data;

            if (task === "qa") {

                data = await callApi(
                    "/qa",
                    { question: text }
                );

                renderTextResult(data.result);

            } else if (task === "explain") {

                data = await callApi(
                    "/explain",
                    { text: text }
                );

                renderTextResult(data.result);

            } else if (task === "quiz") {

                data = await callApi(
                    "/quiz",
                    { text: text }
                );

                renderQuiz(data.questions);

            } else if (task === "summarize") {

                data = await callApi(
                    "/summarize",
                    { text: text }
                );

                renderTextResult(data.result);

            } else if (task === "learn") {

                data = await callApi(
                    "/learn/recommendations",
                    {
                        topic: text,
                        level: levelSelect.value
                    }
                );

                renderTextResult(data.result);

            } else {

                throw new Error(
                    "Unknown task selected."
                );
            }

            resultSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        } catch (error) {

            console.error(
                "EduGenie error:",
                error
            );

            resultContainer.innerHTML = `
                <div class="error">

                    <strong>Error:</strong>

                    ${escapeHtml(error.message)}

                </div>
            `;

        } finally {

            setLoading(false);
        }
    }
);

copyButton.addEventListener(
    "click",
    async function () {

        const text =
            resultContainer.innerText.trim();

        if (!text) {
            return;
        }

        try {

            await navigator.clipboard.writeText(text);

            const originalText =
                copyButton.textContent;

            copyButton.textContent =
                "Copied!";

            setTimeout(
                function () {
                    copyButton.textContent =
                        originalText;
                },
                1500
            );

        } catch (error) {

            console.error(
                "Copy failed:",
                error
            );

            alert(
                "Unable to copy the result."
            );
        }
    }
);

taskSelect.addEventListener(
    "change",
    updateTaskUI
);

updateTaskUI();