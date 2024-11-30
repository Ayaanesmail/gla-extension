// index.js

document.addEventListener("DOMContentLoaded", function () {
  // Define all icons and add event listeners for hover effects
  const icons = [
    { id: 'menu-icon', active: 'Menu_Active.png', inactive: 'Menu_Inactive.png', fn: executeFeature1 },
    { id: 'summary-icon', active: 'Summary_Active.png', inactive: 'Summary_Inactive.png', fn: executeFeature2 },
    { id: 'track-icon', active: 'Track_Active.png', inactive: 'Track_Inactive.png', fn: executeFeature3 },
    { id: 'save-icon', active: 'Save_Active.png', inactive: 'Save_Inactive.png', fn: executeFeature4 },
    { id: 'dashboard-icon', active: 'Dashboard_Active.png', inactive: 'Dashboard_Inactive.png', fn: executeFeature5 }
  ];

  icons.forEach(icon => {
    const el = document.getElementById(icon.id);
    el.addEventListener('mouseover', () => el.src = icon.active);
    el.addEventListener('mouseout', () => el.src = icon.inactive);
    el.addEventListener('click', icon.fn);
  });

  // Update page info when tab changes
  function updatePageInfo() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const currentTab = tabs[0];
      if (currentTab) {
        document.getElementById('page-title').textContent = currentTab.title || 'No title available';
        document.getElementById('page-url').textContent = currentTab.url || 'No URL available';
      } else {
        document.getElementById('page-title').textContent = 'No active tab found';
        document.getElementById('page-url').textContent = '';
      }
    });
  }

  // Initial page info update
  updatePageInfo();

  // Listen for messages from content script
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'scrape') {
      document.getElementById('page-title').textContent = message.data.title;
      document.getElementById('page-url').textContent = window.location.href;
    }
  });

  // Listen for tab updates
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete') {
      updatePageInfo();
    }
  });

  // Listen for tab activation changes
  chrome.tabs.onActivated.addListener(() => {
    updatePageInfo();
  });

  // Add event listeners for summary buttons
  document.getElementById('s-summary').addEventListener('click', () => generateSummary('s'));
  document.getElementById('m-summary').addEventListener('click', () => generateSummary('m'));
  document.getElementById('l-summary').addEventListener('click', () => generateSummary('l'));

  async function generateSummary(size) {
    console.log(`Generating ${size} summary...`);

    // Show loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    loadingIndicator.style.display = 'block';

    try {
        // Get current tab URL
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        const currentTab = tabs[0];
        
        console.log('Current URL:', currentTab.url);
        
        // Extract video ID from YouTube URL
        const videoId = extractVideoId(currentTab.url);
        if (!videoId) {
            alert('Please navigate to a YouTube video page');
            loadingIndicator.style.display = 'none';
            return;
        }
        
        console.log('Video ID:', videoId);

      const response = await fetch('http://35.223.216.53:8000/summarize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                video_id: videoId,
                summary_size: size,
                search_query: currentTab.title || ''
            })
        });


        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData}`);
        }

        const data = await response.json();
        console.log('Received response:', data);
        displaySummaries(data.summaries);
    } catch (error) {
        console.error('Error:', error);
        alert(`Failed to generate summary: ${error.message}`);
    } finally {
        // Hide loading indicator
        loadingIndicator.style.display = 'none';
    }
  }

  function extractVideoId(url) {
    const urlObj = new URL(url);
    if (urlObj.hostname === 'www.youtube.com' || urlObj.hostname === 'youtube.com') {
      return urlObj.searchParams.get('v');
    }
    return null;
  }

  function displaySummaries(summaries) {
    const contentDiv = document.getElementById('content');
    const summaryHtml = summaries.map((summary) => {
        // Create a temporary div to handle HTML content properly
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = summary.summary;
        const fullText = tempDiv.innerHTML;

        // Get the first sentence (handles both plain text and HTML content)
        const firstPeriodIndex = fullText.indexOf('.');
        const firstQuestionIndex = fullText.indexOf('?');
        const firstExclamationIndex = fullText.indexOf('!');

        // Find the earliest sentence ending that exists
        const indices = [firstPeriodIndex, firstQuestionIndex, firstExclamationIndex]
            .filter(index => index !== -1);

        let previewText = fullText; // Default to full text if no sentence ending found
        if (indices.length > 0) {
            const firstSentenceEnd = Math.min(...indices);
            previewText = fullText.substring(0, firstSentenceEnd + 1);
        }

        return `
            <div class="summary-item">
                <div class="time-range">${summary.time_range}</div>
                <div class="summary-text">
                    <div class="preview-text">${previewText}</div>
                    <div class="full-text" style="display: none;">${fullText}</div>
                </div>
            </div>
        `;
    }).join('');

    // Create or update summaries container
    let summariesContainer = document.getElementById('summaries-container');
    if (!summariesContainer) {
        summariesContainer = document.createElement('div');
        summariesContainer.id = 'summaries-container';
        contentDiv.appendChild(summariesContainer);
    }
    summariesContainer.innerHTML = summaryHtml;
  }
});

// Functions to handle icon clicks
function executeFeature1() {
  console.log("Feature 1 activated");
  // Implement Feature 1 functionality
}

function executeFeature2() {
  console.log("Feature 2 activated");
  // Implement Feature 2 functionality
}

function executeFeature3() {
  console.log("Feature 3 activated");
  // Implement Feature 3 functionality
}

function executeFeature4() {
  console.log("Feature 4 activated");
  // Implement Feature 4 functionality
}

function executeFeature5() {
  console.log("Feature 5 activated");
  // Implement Feature 5 functionality
}
