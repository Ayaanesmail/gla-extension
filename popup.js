// // Listen for messages from the content script
// chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
//     // If we received the video title, update the popup display
//     if (message.videoTitle) {
//         document.getElementById('title').textContent = message.videoTitle;
//     }
// });

let videoTitle = 'Unknown Video Title';

// Listen for messages from the content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.videoTitle) {
        videoTitle = message.videoTitle;
        document.getElementById('title').textContent = message.videoTitle;
    }
    // Handle the VIDEO_TITLE action message as well
    if (message.action === 'VIDEO_TITLE') {
        videoTitle = message.title;
        document.getElementById('title').textContent = message.title;
    }
});

// Add event listener for quiz generation
document.getElementById('generateQuizBtn').addEventListener('click', () => {
    const age = document.getElementById('ageInput').value;
    const gradeLevel = document.getElementById('gradeInput').value;
    const difficulty = document.getElementById('difficultySelect').value;

    // Validate inputs
    if (!age || !gradeLevel || !difficulty) {
        alert('Please fill in all fields');
        return;
    }

    // Make API request to generate quiz
    fetch('http://localhost:8000/generate_quiz', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            video_title: videoTitle,
            age: parseInt(age, 10),
            grade_level: parseInt(gradeLevel, 10),
            difficulty: difficulty
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const quizContainer = document.getElementById('quizContainer');
        quizContainer.innerText = data.quiz;
    })
    .catch(error => {
        console.error("Error fetching quiz:", error);
        const quizContainer = document.getElementById('quizContainer');
        quizContainer.innerText = 'Error generating quiz. Please try again.';
    });
});
