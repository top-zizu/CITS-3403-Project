const navItems = document.querySelectorAll(".nav-links li");
const filterButtons = document.querySelectorAll(".filters button");
const createBtn = document.querySelector(".primary-btn");
const debateContainer = document.querySelector(".debates");

// NAVIGATION
navItems.forEach(item => {
  item.addEventListener("click", () => {
    navItems.forEach(i => i.classList.remove("active-nav"));
    item.classList.add("active-nav");
  });
});

// FILTER BUTTONS
filterButtons.forEach(button => {
  button.addEventListener("click", () => {
    filterButtons.forEach(btn => btn.classList.remove("active"));
    button.classList.add("active");
  });
});

// CREATE DEBATE
createBtn.addEventListener("click", () => {
  const title = prompt("Enter debate title:");
  if (!title || title.trim() === "") return;

  const debateHTML = `
    <article class="debate-card" data-user-vote="neutral">
      <p class="time">Ends in 24 hours</p>
      <h2>${title}</h2>

      <div class="votes">
        <div class="agree">
          <p>Agree</p>
          <strong>0</strong>
          <div>0%</div>
        </div>

        <div class="disagree">
          <p>Disagree</p>
          <strong>0</strong>
          <div>0%</div>
        </div>
      </div>

      <div class="progress-bar">
        <div class="agree-bar" style="width: 50%"></div>
        <div class="disagree-bar" style="width: 50%"></div>
      </div>

      <button class="comments-btn">
        <i class="fa-regular fa-comment"></i>
        <span class="comment-count">0</span> Comments
      </button>

      <section class="comments-section hidden">
        <div class="comment-form">
          <textarea maxlength="300" placeholder="Add a comment..."></textarea>
          <button class="post-btn">Post</button>
        </div>
      </section>
    </article>
  `;

  debateContainer.insertAdjacentHTML("beforeend", debateHTML);
});

// ========================
// VOTING LOGIC (SWITCHABLE)
// ========================
document.addEventListener("click", event => {
  const voteBox = event.target.closest(".agree, .disagree");
  if (!voteBox) return;

  const card = voteBox.closest(".debate-card");

  const agreeBox = card.querySelector(".agree");
  const disagreeBox = card.querySelector(".disagree");

  const agreeNumber = card.querySelector(".agree strong");
  const disagreeNumber = card.querySelector(".disagree strong");

  let agreeVotes = parseInt(agreeNumber.textContent);
  let disagreeVotes = parseInt(disagreeNumber.textContent);

  const oldVote = card.dataset.userVote;
  const newVote = voteBox.classList.contains("agree") ? "agree" : "disagree";

  // Clicking same vote → do nothing
  if (oldVote === newVote) return;

  // Remove old vote
  if (oldVote === "agree") agreeVotes--;
  if (oldVote === "disagree") disagreeVotes--;

  // Add new vote
  if (newVote === "agree") agreeVotes++;
  else disagreeVotes++;

  // Save new vote
  card.dataset.userVote = newVote;

  // Update numbers
  agreeNumber.textContent = agreeVotes;
  disagreeNumber.textContent = disagreeVotes;

  const total = agreeVotes + disagreeVotes;

  const agreePercent = total === 0 ? 0 : ((agreeVotes / total) * 100).toFixed(1);
  const disagreePercent = total === 0 ? 0 : ((disagreeVotes / total) * 100).toFixed(1);

  card.querySelector(".agree div").textContent = agreePercent + "%";
  card.querySelector(".disagree div").textContent = disagreePercent + "%";

  card.querySelector(".agree-bar").style.width = agreePercent + "%";
  card.querySelector(".disagree-bar").style.width = disagreePercent + "%";

  // UI highlight
  agreeBox.classList.remove("selected-vote");
  disagreeBox.classList.remove("selected-vote");
  voteBox.classList.add("selected-vote");
});

// ========================
// COMMENTS TOGGLE
// ========================
document.addEventListener("click", event => {
  const commentsBtn = event.target.closest(".comments-btn");

  if (commentsBtn) {
    const card = commentsBtn.closest(".debate-card");
    const section = card.querySelector(".comments-section");
    section.classList.toggle("hidden");
  }
});

// ========================
// POST COMMENTS
// ========================
document.addEventListener("click", event => {
  const postBtn = event.target.closest(".post-btn");
  if (!postBtn) return;

  const card = postBtn.closest(".debate-card");
  const input = card.querySelector(".comment-form textarea");

  if (input.value.trim() === "") return;

  const userVote = card.dataset.userVote;

  let commentClass = "neutral-comment";
  let label = "Neutral";

  if (userVote === "agree") {
    commentClass = "blue-comment";
    label = "Agree";
  }

  if (userVote === "disagree") {
    commentClass = "red-comment";
    label = "Disagree";
  }

  const newComment = document.createElement("div");
  newComment.className = "comment " + commentClass;

  newComment.innerHTML = `
    <strong>
      CurrentUser
      <span>${label}</span>
    </strong>
    <p>${input.value}</p>
  `;

  card.querySelector(".comments-section").appendChild(newComment);

  input.value = "";
  updateCommentCount(card);
});

// ========================
// UPDATE COMMENT COUNT
// ========================
function updateCommentCount(card) {
  const count = card.querySelectorAll(".comment").length;
  card.querySelector(".comment-count").textContent = count;
}
