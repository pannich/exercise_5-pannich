
/* For room.html */

// TODO: When a chat room page first loads, clear any sample messages out of the chat histoy. [1 point] ?

// TODO: Fetch the list of existing chat messages.
// POST to the API when the user posts a new message.
// Automatically poll for new messages on a regular interval.
// Allow changing the name of a room

var curr_message_len = 0

// addeventlistener: https://www.w3schools.com/js/js_htmldom_eventlistener.asp
// DOMContentLoaded: https://developer.mozilla.org/en-US/docs/Web/API/Document/DOMContentLoaded_event

document.addEventListener('DOMContentLoaded', () => {
  // room.html
  // submit message
  const btn = document.getElementById('submitbtn');
  if (btn) {
    btn.addEventListener('click', postMessage);
  }

  // edit room name
  const editIcon = document.querySelector('.display .material-symbols-outlined');
  if (editIcon) {
    editIcon.addEventListener('click', hide_room_edit);
  }
  const saveIcon = document.querySelector('.edit .material-symbols-outlined');
  if (editIcon) {
    editIcon.addEventListener('click', updateRoomName);
  }


  // profile.html
  // edit profile
  const update_username = document.querySelector('button.username');
  if (update_username) {
    update_username.addEventListener('click', updateUserName);
  }
  const update_password = document.querySelector('button.password');
  if (update_password) {
    update_password.addEventListener('click', updatePassword);
  }
});

function hide_room_edit() {
  this.closest('.display').classList.add('hide');
  document.querySelector('.edit').classList.remove('hide');
}

async function postMessage() {
  var resultsContainer = document.body.querySelector(".messages");
  resultsContainer.innerHTML = '';

  const bodyValue = document.querySelector('textarea[name="comment"]').value;

  let new_message
  try {
    const response = await fetch(`/api/messages/post`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY
      },
      body: JSON.stringify({
        "body": bodyValue,
        "room_id": room_id,
        "user_id": WATCH_PARTY_USER_ID
      }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    new_message = await response.json();
    console.log(new_message);
  } catch (error) {
    console.error('Failed to fetch messages:', error);
  }
  return;
}

async function getMessages(initialLoad=false) {
  let messages;
  try {
    const response = await fetch(`/api/messages?room_id=${room_id}`, {
      method: 'GET',
      headers: {
        'X-API-Key': WATCH_PARTY_API_KEY
      },
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    messages = await response.json();
    console.log(messages); //log
  } catch (error) {
    console.error('Failed to fetch messages:', error);
  }

  var resultsContainer = document.body.querySelector(".messages");
  if (initialLoad) {
    // clear sample messages in the 1st fetch
    resultsContainer.innerHTML = '';
    initialLoad = false;
  }

  var latest_messages_len = messages.length;
  console.log(latest_messages_len);

  if(latest_messages_len > curr_message_len){
    // update a new message
    messages.slice(curr_message_len, latest_messages_len).forEach(message => {
    const newMsgClass = document.createElement("message");

    const authorElement = document.createElement("author");
    authorElement.textContent = message["user_name"];
    const contentElement = document.createElement("content");
    contentElement.textContent = message["body"];

    newMsgClass.appendChild(authorElement);
    newMsgClass.appendChild(contentElement);

    resultsContainer.appendChild(newMsgClass);

    curr_message_len = latest_messages_len;

   });
  }
  return;
}

function startMessagePolling() {
  console.log(WATCH_PARTY_USER_ID);
  console.log(WATCH_PARTY_API_KEY);

  let initialLoad = true;
  getMessages(initialLoad);

  // TODO
  setInterval(async () => {
    await getMessages();
  }, 10000);
  return;
}

async function updateRoomName() {
  var new_room_name = document.querySelector('.edit input').value;
  try {
    const response = await fetch(`/api/rooms/changename`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY
      },
      body: JSON.stringify({
        "room_id": room_id,
        "new_room_name": new_room_name
      }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    resp_message = await response.json();
    // console.log(resp_message);

    document.querySelector('.roomName').textContent = new_room_name; // Update the display name instantly
    this.closest('.edit').classList.add('hide');
    document.querySelector('.display').classList.remove('hide');

  } catch (error) {
    console.error('Failed to fetch messages:', error);
  }
  return;
}

/* For profile.html */

// TODO: Allow updating the username and password
async function updateUserName() {
  var new_user_name = document.querySelector('input.username').value;
  console.log(new_user_name);
  try {
    const response = await fetch(`/api/user/name`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY
      },
      body: JSON.stringify({
        "user_name": new_user_name
      }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    resp_message = await response.json();
    console.log(resp_message);

  } catch (error) {
    console.error('Failed to fetch messages:', error);
  }
  return;
}

async function updatePassword() {
  var new_password = document.querySelector('input.password').value;
  try {
    const response = await fetch(`/api/user/password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': WATCH_PARTY_API_KEY
      },
      body: JSON.stringify({
        "password": new_password
      }),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    resp_message = await response.json();
    console.log(resp_message);

  } catch (error) {
    console.error('Failed to fetch messages:', error);
  }
  return;
}
