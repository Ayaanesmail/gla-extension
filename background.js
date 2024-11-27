let scrapedData = {};

// Listener to receive messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'scrape' && message.data) {
    scrapedData[sender.tab.id] = message.data;
  } else if (message.action === 'getScrapedData') {
    const tabId = message.tabId;
    sendResponse(scrapedData[tabId] || {});
  }
});

chrome.runtime.onInstalled.addListener(() => {
  // Initialize extension
});

chrome.runtime.onStartup.addListener(() => {
  // Re-initialize extension
});

// No need to set side panel options if declared in the manifest
