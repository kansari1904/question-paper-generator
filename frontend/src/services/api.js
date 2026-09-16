const API_BASE_URL = import.meta.env.VITE_BASE_URL;

async function handleResponse(response, fallbackMessage) {
  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : fallbackMessage
    );
  }

  return data;
}

export async function generatePaper(payload, seed = 42) {
  const response = await fetch(
    `${API_BASE_URL}/paper/generate?seed=${seed}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(
    response,
    "Failed to generate paper."
  );
}

export async function swapQuestion(paperId, questionId) {
  const response = await fetch(
    `${API_BASE_URL}/paper/swap`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        paper_id: paperId,
        question_id: questionId,
      }),
    }
  );

  return handleResponse(
    response,
    "Failed to swap question."
  );
}

export async function getPaper(paperId) {
  const response = await fetch(
    `${API_BASE_URL}/paper/${paperId}`
  );

  return handleResponse(
    response,
    "Failed to load paper."
  );
}