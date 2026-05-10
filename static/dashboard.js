document.addEventListener("DOMContentLoaded", () => {
    const filterButtons = document.querySelectorAll(".filters button");
    const debateContainer = document.querySelector(".debates");
  
    if (!debateContainer) return;
  
    const debates = [
      {
        title: "Remote work is better than office work",
        status: "active",
        time: "Ends in 24 hours",
        agree: 72,
        disagree: 28,
        comments: 12,
        tags: ["work", "lifestyle"]
      },
      {
        title: "AI tools should be allowed in university assessments",
        status: "active",
        time: "Ends in 12 hours",
        agree: 55,
        disagree: 45,
        comments: 8,
        tags: ["technology", "education"]
      },
      {
        title: "Social media has a net negative impact on society",
        status: "active",
        time: "Ends in 8 hours",
        agree: 64,
        disagree: 36,
        comments: 18,
        tags: ["technology", "society"]
      },
      {
        title: "Cats are better pets than dogs",
        status: "ended",
        time: "Ended",
        agree: 81,
        disagree: 19,
        comments: 6,
        tags: ["animals", "lifestyle"]
      }
    ];
  
    function renderDebates(filter = "all") {
      const filtered =
        filter === "all"
          ? debates
          : debates.filter(debate => debate.status === filter);
  
      debateContainer.innerHTML = filtered.map(debate => {
        const total = debate.agree + debate.disagree;
        const agreePercent = total === 0 ? 0 : ((debate.agree / total) * 100).toFixed(1);
        const disagreePercent = total === 0 ? 0 : ((debate.disagree / total) * 100).toFixed(1);
  
        return `
          <article class="debate-card" data-user-vote="neutral" data-status="${debate.status}">
            <p class="time">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              ${debate.time}
            </p>
  
            <h2>${debate.title}</h2>
  
            <div class="votes">
              <div class="agree">
                <p>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M7 10v11"/>
                    <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>
                  </svg>
                  Agree
                </p>
                <strong>${debate.agree}</strong>
                <div>${agreePercent}%</div>
              </div>
  
              <div class="disagree">
                <p>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17 14V3"/>
                    <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/>
                  </svg>
                  Disagree
                </p>
                <strong>${debate.disagree}</strong>
                <div>${disagreePercent}%</div>
              </div>
            </div>
  
            <div class="progress-bar">
              <div class="agree-bar" style="width: ${agreePercent}%"></div>
              <div class="disagree-bar" style="width: ${disagreePercent}%"></div>
            </div>
  
            <div class="card-footer">
              <button class="comments-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <span class="comment-count">${debate.comments}</span> Comments
              </button>
  
              <div class="card-tags">
                ${debate.tags.map(tag => `
                  <span class="card-tag">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                      stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82Z"/>
                      <circle cx="7.5" cy="7.5" r=".5"/>
                    </svg>
                    ${tag}
                  </span>
                `).join("")}
              </div>
            </div>
  
            <section class="comments-section hidden">
              <div class="comment-form">
                <textarea maxlength="300" placeholder="Add a comment..."></textarea>
                <button class="post-btn">Post</button>
              </div>
            </section>
          </article>
        `;
      }).join("");
    }
  
    filterButtons.forEach(button => {
      button.addEventListener("click", () => {
        filterButtons.forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
  
        const filter = button.dataset.filter || button.textContent.trim().toLowerCase();
        renderDebates(filter);
      });
    });  
    renderDebates("all");
  });