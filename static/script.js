document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chatInput");
  const sendChatBtn = document.getElementById("sendChatBtn");
  const chatBox = document.getElementById("chatBox");

  let userId = "default"; // In production, generate a unique user ID
  let typingIndicator;
  let map, markers = [];

  // Initialize Leaflet map
  function initMap() {
    map = L.map('map').setView([4.890, 114.941], 12); // Brunei default
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);
  }
  initMap();

  async function sendChat(message) {
    if (!message) return;
    addChatMessage("user", message);
    chatInput.value = "";
    showTypingIndicator();

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, user_id: userId })
      });

      const data = await res.json();
      hideTypingIndicator();

      if (data.reply) {
        addChatMessage("bot", data.reply);

        // Inject preferences form listener
        const form = document.getElementById("preferencesForm");
        if (form) {
          form.addEventListener("submit", e => {
            e.preventDefault();
            const formData = new FormData(form);
            const prefs = {
              budget: formData.get("budget"),
              travel_style: formData.get("travel_style"),
              interests: formData.getAll("interests")
            };
            sendChat(JSON.stringify({ preferences: prefs }));
          });
        }

        // Confirm button listener
        const confirmBtn = document.getElementById("confirmTripBtn");
        if (confirmBtn) {
          confirmBtn.addEventListener("click", () => sendChat("Generate itinerary"));
        }
      }

      // Render itinerary if returned
      if (data.itinerary) renderItinerary(data.itinerary);

    } catch (err) {
      hideTypingIndicator();
      addChatMessage("bot", "⚠️ Error: could not get response.");
    }
  }

  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendChat(chatInput.value.trim());
  });
  sendChatBtn.addEventListener("click", () => sendChat(chatInput.value.trim()));

  // ...existing code...

function addChatMessage(sender, text) {
  const msg = document.createElement("div");
  msg.className = sender === "user" ? "chat-user" : "chat-bot";
  msg.innerHTML = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;

  // Attach handlers to dynamic preference buttons
  msg.querySelectorAll(".preference-btn").forEach(btn => {
    btn.onclick = () => {
      const preference_type = btn.getAttribute("data-type");
      const value = btn.getAttribute("data-value");
      sendChat(JSON.stringify({ preference_type, value }));
    };
  });
}
// ...existing code...

  function showTypingIndicator() {
    typingIndicator = document.createElement("div");
    typingIndicator.className = "chat-bot typing";
    typingIndicator.textContent = "JalanJalan.AI is thinking...";
    chatBox.appendChild(typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function hideTypingIndicator() {
    if (typingIndicator) {
      chatBox.removeChild(typingIndicator);
      typingIndicator = null;
    }
  }

  // Render POIs/hotels/restaurants on map
  function renderItinerary(itinerary) {
    clearMarkers();
    itinerary.forEach(item => {
      const content = `<b>${item.time || ""}</b>: ${item.title}<br>${item.description}`;
      addChatMessage("bot", content);

      if (item.lat && item.lon) {
        const marker = L.marker([item.lat, item.lon]).addTo(map)
          .bindPopup(`<b>${item.title}</b><br>${item.description}`);
        markers.push(marker);
      }
    });

    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.5));
    }
  }

  function clearMarkers() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
  }
});
