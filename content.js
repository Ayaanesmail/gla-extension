// content.js

// Create the floating icon
const icon = document.createElement('div');
icon.id = 'gla-icon';
icon.style.position = 'fixed';
icon.style.bottom = '20px';
icon.style.right = '20px';
icon.style.width = '50px';
icon.style.height = '50px';
icon.style.backgroundImage = 'url(' + chrome.runtime.getURL('GLA_icon.png') + ')';
icon.style.backgroundSize = 'contain';
icon.style.backgroundRepeat = 'no-repeat';
icon.style.cursor = 'pointer';
icon.style.zIndex = '10000'; // Ensure it appears above other elements
icon.style.transition = 'opacity 0.3s';
icon.style.opacity = '0.7';
icon.addEventListener('mouseover', () => (icon.style.opacity = '1.0'));
icon.addEventListener('mouseout', () => (icon.style.opacity = '0.7'));

// Append the icon to the page
document.body.appendChild(icon);

// Handling click events for scraping and sending YouTube data
icon.addEventListener('click', () => {
  if (
    window.location.hostname.includes('youtube.com') &&
    window.location.pathname.includes('watch')
  ) {
    // Scrape YouTube video title and description
    const videoTitleElement = document.querySelector('h1.title') ||
                              document.querySelector('h1.title yt-formatted-string');
    const videoDescriptionElement = document.querySelector('#description') ||
                                    document.querySelector('div#description yt-formatted-string');

    const videoTitle = videoTitleElement?.innerText.trim() || 'No title found';
    const videoDescription = videoDescriptionElement?.innerText.trim() || 'No description found';

    // Log the scraped data to the console
    console.log('YouTube Video Title:', videoTitle);
    console.log('YouTube Video Description:', videoDescription);

    // Send scraped data to background script
    chrome.runtime.sendMessage({
      action: 'scrape',
      data: {
        title: videoTitle,
        description: videoDescription,
      },
    });
  } else {
    // Scrape text from other pages
    const pageText = Array.from(document.querySelectorAll('p'))
      .map((p) => p.textContent)
      .join(' ');

    console.log('Page Text:', pageText);

    // Send scraped data to background script
    chrome.runtime.sendMessage({
      action: 'scrape',
      data: {
        text: pageText,
      },
    });
  }
});

// Function to extract the transcript
async function getTranscript(videoId) {
  try {
    const response = await fetch(`https://www.youtube.com/api/timedtext?lang=en&v=${videoId}`);
    const transcriptXml = await response.text();

    // Parse the XML to extract text
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(transcriptXml, "text/xml");
    const texts = xmlDoc.getElementsByTagName("text");

    let transcript = "";
    for (let i = 0; i < texts.length; i++) {
      const text = texts[i].textContent.replace(/\n/g, " ");
      transcript += text + " ";
    }

    return transcript.trim();
  } catch (error) {
    console.error("Error fetching transcript:", error);
    return null;
  }
}

// Function to extract video ID from URL
function getVideoIdFromUrl(url) {
  const urlObj = new URL(url);
  return urlObj.searchParams.get('v');
}

// Listen for messages from the popup script
chrome.runtime.onMessage.addListener(async (message, sender, sendResponse) => {
  if (message.action === 'getTranscript') {
    const videoId = getVideoIdFromUrl(window.location.href);

    if (videoId) {
      const transcript = await getTranscript(videoId);
      if (transcript) {
        sendResponse({ success: true, transcript });
      } else {
        sendResponse({ success: false, error: 'Transcript not available.' });
      }
    } else {
      sendResponse({ success: false, error: 'No video ID found in the URL.' });
    }

    // Indicate that we'll respond asynchronously
    return true;
  }
});
