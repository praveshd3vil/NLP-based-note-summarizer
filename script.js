const API_BASE_URL = "http://127.0.0.1:8000";
const SUMMARIZE_ENDPOINT = `${API_BASE_URL}/summarize`;

const notesInput = document.getElementById("notesInput");
const charCount = document.getElementById("charCount");
const summarizeBtn = document.getElementById("summarizeBtn");

const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");
const errorState = document.getElementById("errorState");
const errorMessage = document.getElementById("errorMessage");
const resultState = document.getElementById("resultState");
const summaryText = document.getElementById("summaryText");

// counts character in input

notesInput.addEventListener("input", () => {
  const count = notesInput.value.length;
  charCount.textContent = `${count.toLocaleString()} character${count === 1 ? "" : "s"}`;
});

function showState(stateName) {
  const states = {
    empty: emptyState,
    loading: loadingState,
    error: errorState,
    result: resultState,
  };

  for (const [name, element] of Object.entries(states)) {
    element.classList.toggle("hidden", name !== stateName);
  }
}

function setButtonLoading(isLoading) {
  summarizeBtn.disabled = isLoading;
  summarizeBtn.querySelector(".btn-label").textContent = isLoading
    ? "Summarizing…"
    : "Summarize";
}

async function handleSummarize() {
  const text = notesInput.value.trim();

  if (!text) {
    errorMessage.textContent = "Please enter some text before summarizing.";
    showState("error");
    return;
  }

  setButtonLoading(true);
  showState("loading");

  try {
    const response = await fetch(SUMMARIZE_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const message =
        (data && data.detail) ||
        `Request failed with status ${response.status}.`;
      throw new Error(message);
    }

    if (!data || !data.summary) {
      throw new Error("The server returned an unexpected response.");
    }

    summaryText.textContent = data.summary;
    showState("result");

  } catch (err) {

    if (err instanceof TypeError) {
      errorMessage.textContent =
        "Couldn't reach the summarizer backend. Make sure the FastAPI server is running on http://127.0.0.1:8000.";
    } else {
      errorMessage.textContent = err.message || "Something went wrong while summarizing.";
    }
    showState("error");

  } finally {
    setButtonLoading(false);
  }
}

summarizeBtn.addEventListener("click", handleSummarize);

// Optional UX nicety: allow Ctrl+Enter / Cmd+Enter inside the textarea
// to trigger summarization without reaching for the mouse.
notesInput.addEventListener("keydown", (e) => {
  const isSubmitCombo = (e.ctrlKey || e.metaKey) && e.key === "Enter";
  if (isSubmitCombo) {
    e.preventDefault();
    handleSummarize();
  }
});
