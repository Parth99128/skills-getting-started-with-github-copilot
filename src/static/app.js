document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Create participants list HTML with delete icon
        let participantsHTML = "<ul class='participants-list'>";
        if (details.participants.length === 0) {
          participantsHTML += "<li class='no-participants'>No participants yet</li>";
        } else {
          details.participants.forEach(email => {
            participantsHTML += `<li class="participant-item" data-activity="${name}" data-email="${email}">
              <span class="participant-email">${email}</span>
              <span class="delete-participant" title="Remove participant">&times;</span>
            </li>`;
          });
        }
        participantsHTML += "</ul>";

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <strong>Participants:</strong>
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add event listeners for delete icons after rendering
        setTimeout(() => {
          const deleteIcons = activityCard.querySelectorAll('.delete-participant');
          deleteIcons.forEach(icon => {
            icon.addEventListener('click', async (e) => {
              const li = e.target.closest('.participant-item');
              const activityName = li.getAttribute('data-activity');
              const participantEmail = li.getAttribute('data-email');
              try {
                const response = await fetch(`/activities/${encodeURIComponent(activityName)}/signup?email=${encodeURIComponent(participantEmail)}`, {
                  method: 'DELETE'
                });
                if (response.ok) {
                  // Refresh activities to update availability numbers and UI
                  fetchActivities();
                } else {
                  const result = await response.json();
                  alert(result.detail || 'Failed to remove participant');
                }
              } catch (error) {
                alert('Failed to remove participant');
              }
            });
          });
        }, 0);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        
        // Refresh the activities list to show the newly added participant
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
