const followBtn = document.getElementById('profile-follow-btn');
  const profileCsrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

  followBtn?.addEventListener('click', () => {
    const userId = followBtn.dataset.userId;
    const isFollowing = followBtn.dataset.following === 'true';

    fetch(`/api/users/${userId}/follow`, {
      method: isFollowing ? 'DELETE' : 'POST',
      headers: { 'X-CSRFToken': profileCsrfToken },
    })
      .then(response => response.json().then(data => ({ response, data })))
      .then(({ response, data }) => {
        if (!response.ok || data.error) {
          alert(data.error || 'Could not update follow status.');
          return;
        }

        followBtn.dataset.following = String(data.following);
        followBtn.classList.toggle('following', data.following);
        followBtn.textContent = data.following
          ? 'Following'
          : (data.user?.follows_you ? 'Follow back' : 'Follow');

        const followerCount = document.getElementById('profile-follower-count');
        if (followerCount && data.user) {
          followerCount.textContent = data.user.follower_count;
        }
      })
      .catch(() => alert('Could not update follow status.'));
  });