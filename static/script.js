// script.js

document.addEventListener('DOMContentLoaded', () => {
    const budgetButtons = document.querySelectorAll('.budget-btn');
    const interestsInput = document.getElementById('interests-input');
    const interestsTagsContainer = document.getElementById('interests-tags');
    const tripForm = document.getElementById('trip-form');
    const loadingIndicator = document.getElementById('loading-indicator');
    const itineraryOutput = document.getElementById('itinerary-output');

    let selectedBudget = '';
    let interests = [];

    // Handle budget button selection
    budgetButtons.forEach(button => {
        button.addEventListener('click', () => {
            budgetButtons.forEach(btn => btn.classList.remove('selected'));
            button.classList.add('selected');
            selectedBudget = button.dataset.budget;
        });
    });

    // Handle interests input
    interestsInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && interestsInput.value.trim() !== '') {
            event.preventDefault();
            const newInterest = interestsInput.value.trim();
            if (!interests.includes(newInterest)) {
                interests.push(newInterest);
                renderInterests();
            }
            interestsInput.value = '';
        }
    });

    // Render interests tags
    function renderInterests() {
        // Clear existing tags, but keep the input field
        const existingTags = interestsTagsContainer.querySelectorAll('.tag');
        existingTags.forEach(tag => tag.remove());

        interests.forEach(interest => {
            const tag = document.createElement('span');
            tag.classList.add('tag');
            tag.innerHTML = `${interest} <span class="close" data-interest="${interest}">&times;</span>`;
            interestsTagsContainer.insertBefore(tag, interestsInput);
        });
    }

    // Handle removing interests
    interestsTagsContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('close')) {
            const interestToRemove = event.target.dataset.interest;
            interests = interests.filter(interest => interest !== interestToRemove);
            renderInterests();
        }
    });

    // Handle form submission
    tripForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        loadingIndicator.style.display = 'block';
        itineraryOutput.innerHTML = ''; // Clear previous results

        const destination = document.getElementById('destination').value;
        const days = document.getElementById('days').value;
        const travelStyle = document.getElementById('travel-style').value;

        const data = {
            budget: selectedBudget,
            interests: interests.join(', '),
            travel_style: travelStyle,
            days: parseInt(days),
            destination: destination
        };

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.error) {
                itineraryOutput.innerHTML = `<p class="error">Error: ${result.error}</p>`;
            } else {
                renderItinerary(result);
            }
        } catch (error) {
            console.error('Error:', error);
            itineraryOutput.innerHTML = '<p class="error">An unexpected error occurred. Please try again.</p>';
        } finally {
            loadingIndicator.style.display = 'none';
        }
    });

    function renderItinerary(itineraryData) {
        let html = '<h2>Your Custom Itinerary</h2>';

        // Render Accommodation
        if (itineraryData.accommodation && itineraryData.accommodation.length > 0) {
            html += '<div class="accommodation-section"><h3>Accommodation</h3>';
            itineraryData.accommodation.forEach(acc => {
                html += `
                    <div class="accommodation-card">
                        <img src="${acc.photo}" alt="${acc.name}" class="accommodation-photo">
                        <div class="accommodation-details">
                            <h4>${acc.name}</h4>
                            <p><strong>Type:</strong> ${acc.type}</p>
                            <p><strong>Rating:</strong> <span class="rating">${acc.rating}</span></p>
                            <p><strong>Price Range:</strong> ${acc.price_range}</p>
                            <p><strong>Description:</strong> ${acc.description}</p>
                            <a href="${acc.booking_link}" target="_blank" class="map-link">Book Now</a>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Render Itinerary Days
        itineraryData.itinerary.forEach(dayPlan => {
            html += `<div class="day-plan"><h3>${dayPlan.day} - ${dayPlan.theme}</h3>`;
            dayPlan.activities.forEach(activity => {
                html += `
                    <div class="activity-card">
                        <img src="${activity.photo}" alt="${activity.location_name}" class="activity-photo">
                        <div class="activity-details">
                            <h4>${activity.location_name}</h4>
                            <p><strong>Time:</strong> ${activity.time}</p>
                            <p><strong>Description:</strong> ${activity.description}</p>
                            <div class="details-grid">
                                <p><strong>Category:</strong> ${activity.category}</p>
                                <p><strong>Estimated Cost:</strong> ${activity.estimated_cost}</p>
                                <p><strong>Travel Time:</strong> ${activity.travel_time}</p>
                            </div>
                            <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activity.location_name + ', ' + itineraryData.destination)}" target="_blank" class="map-link">View on Map</a>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        });

        itineraryOutput.innerHTML = html;
    }
});
