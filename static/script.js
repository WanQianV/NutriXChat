// Fetch and display all chat histories upon page load

function startNewChat() {
    fetch('/start_new_chat')
        .then(response => response.json())
        .then(data => {
            var chatNumber = data.chat_number;
            var chatSelect = document.getElementById('chat-select');
            var option = document.createElement('option');
            option.value = chatNumber;
            option.text = 'Chat ' + chatNumber;
            chatSelect.appendChild(option);
            // Select the newly created chat
            chatSelect.value = chatNumber;
            // Display chat history for the newly created chat
            viewChatHistory();
        });
}

function sendMessage() {
    var userInput = document.getElementById('user-input').value;
    var chatNumber = document.getElementById('chat-select').value;
    var chatContainer = document.getElementById('chat-container-' + chatNumber);
    var userMessage = document.createElement('div');
    userMessage.className = 'message';
    userMessage.innerHTML = '<strong>You:</strong> ' + userInput;
    chatContainer.appendChild(userMessage);
    document.getElementById('user-input').value = '';

    // Send message to server for processing and get bot's response
    fetch('/send_message', {
        method: 'POST',
        body: new URLSearchParams({
            'message': userInput,
            'chat_number': chatNumber
        }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        var botMessage = document.createElement('div');
        botMessage.className = 'message';
        botMessage.innerHTML = '<strong>Chatbot:</strong> ' + data.bot_response;
        chatContainer.appendChild(botMessage);
    });
}

function viewChatHistory() {
    var chatNumber = document.getElementById('chat-select').value;
    var chatContainer = document.getElementById('chat-containers');
    chatContainer.innerHTML = '';
    var chatHistory = document.createElement('div');
    chatHistory.id = 'chat-container-' + chatNumber;
    chatContainer.appendChild(chatHistory);

    fetch('/get_chat_history', {
        method: 'POST',
        body: new URLSearchParams({
            'chat_number': chatNumber
        }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        data.forEach(message => {
            var messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = '<strong>' + message.sender + ':</strong> ' + message.message;
            chatHistory.appendChild(messageElement);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    fetchAllChatHistories();
});

// Function to fetch and display all chat histories
function fetchAllChatHistories() {
    fetch('/get_all_chat_histories')
        .then(response => response.json())
        .then(data => {
            var chatSelect = document.getElementById('chat-select');
            chatSelect.innerHTML = ''; // Clear existing options
            for (var chatNumber in data) {
                var option = document.createElement('option');
                option.value = chatNumber;
                option.text = 'Chat ' + chatNumber;
                chatSelect.appendChild(option);
            }
            // Display chat history for the first chat by default
            viewChatHistory();
        });
}

// Update chat history when the user selects a different chat
document.getElementById('chat-select').addEventListener('change', function() {
    viewChatHistory();
});

// Function to display chat history for the selected chat
function viewChatHistory() {
    var chatNumber = document.getElementById('chat-select').value;
    var chatContainer = document.getElementById('chat-containers');
    chatContainer.innerHTML = '';
    var chatHistory = document.createElement('div');
    chatHistory.id = 'chat-container-' + chatNumber;
    chatContainer.appendChild(chatHistory);

    fetch('/get_chat_history', {
        method: 'POST',
        body: new URLSearchParams({
            'chat_number': chatNumber
        }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    })
    .then(response => response.json())
    .then(data => {
        data.forEach(message => {
            var messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = '<strong>' + message.sender + ':</strong> ' + message.message;
            chatHistory.appendChild(messageElement);
        });
    });
}

let subMenu = document.getElementById("subMenu");
    let chatHistoryOpen = document.getElementById("chatHistoryOpen");

    // open toggle menu (profile)
    function toggleMenu(){
      subMenu.classList.toggle("open-menu");
    }

    // open chat history
    function chatHistory(){
      chatHistoryOpen.classList.toggle("open-history");
      // rotate icon when click chat history
      var icon = document.getElementById("icon");
      icon.classList.toggle("rotated"); 
    }

  

    // open/ close chat history Responsive
    function openNav() {
      document.getElementById("mySidenav").style.width = "250px";
    }
    function closeNav() {
      document.getElementById("mySidenav").style.width = "0";
    }
    

    // chatbot
    const chatbox = document.querySelector(".chatbox");
    const chatInput = document.querySelector(".chat-input textarea");
    const sendChatBtn = document.querySelector(".chat-input span");

    let userMessage;
    const inputInitHeight = chatInput.scrollHeight;

    const createChatLi = (message, className) => {
      // Create a chat <li> element with passed message and className
      const chatLi = document.createElement("li");
      chatLi.classList.add("chat", className);
      let chatContent = className === "outgoing" ? `<p>${message}</p>` : `<img src="{{ url_for('static', filename='images/Asset 2.png') }}"><p>${message}</p>`;
      
      chatLi.innerHTML = chatContent;
      // chatLi.querySelector("p").textContent = message;
      return chatLi; // return chat <li> element
    }
    
  

    const handleChat = () => {
      userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
      if(!userMessage) return;

      // Clear the input textarea and set its height to default after message was sent
      chatInput.value = "";
      // Append the user's message to the chatbox
      chatbox.appendChild(createChatLi(userMessage, "outgoing"));
      chatInput.style.height = `${inputInitHeight}px`;
     
      
      setTimeout(() => {
        // Display "Thinking..." message while waiting for the response
        chatbox.appendChild(createChatLi("Thinking...", "incoming"));
        chatbox.scrollTo(0, chatbox.scrollHeight);
        // const incomingChatLi = createChatLi("Thinking...", "incoming");
        // chatbox.appendChild(incomingChatLi);
        // generateResponse(incomingChatLi);
      }, 600);
    } 

    // Adjust the height of the input textarea based on its content (max-height: 100px;)
    chatInput.addEventListener("input", () => { 
      chatInput.style.height = `${inputInitHeight}px`;
      chatInput.style.height = `${chatInput.scrollHeight}px`;
    });


    // send message
    chatInput.addEventListener("keydown", function(event) {
      // Check if the viewport width is less than or equal to 550 pixels (responsive)
      const isMobile = window.innerWidth <= 550;

      // If it's a mobile device and Enter key is pressed without Shift key
      if (isMobile && event.key === "Enter" && !event.shiftKey) {
        // Prevent the default behavior of the Enter key (sending the message)
        event.preventDefault();
        // Move the cursor to the next line
        chatInput.value += '\n';
        // Scroll the textarea to the bottom
        chatInput.scrollTop = chatInput.scrollHeight;
      }

      // If Enter key is pressed without Shift key - send message
      // If Enter key is pressed with Shift key - next line
      if (!isMobile && event.key === "Enter" && !event.shiftKey) {
        // Prevent the default behavior of the Enter key (sending the message)
        event.preventDefault();
        handleChat();
      }
    });

    // click the send paper plane icon to send message
    sendChatBtn.addEventListener("click", handleChat);


    // profile customization form open
    var modal = document.getElementById("profileModal");
      
    // Get the button that opens the modal
    var editProfileBtn = document.getElementById("editProfileBtn");
    
    // Function to close the modal
    function closeModal() {
      modal.style.display = 'none';
    }
    
    // When the user clicks the button, open the modal
    editProfileBtn.onclick = function() {
      modal.style.display = "block";
    }

    // Function to show success alert when profile is successfully saved
    function showSuccessAlert() {
      window.alert("Profile updated successfully!");
    }

    // logout confirmation
    function confirmLogout(){
      if(confirm("Are you sure you want to logout?")){
          window.location.href = "/logout"; // Redirect to logout route if user confirms
          window.alert("Logout successfully!");
      } 
      else{
          event.preventDefault(); // Prevent redirect action if user click cancel
      }
    }

    // remove history list
    document.addEventListener('DOMContentLoaded', function() {
      var trashIcons = document.querySelectorAll('.fa-trash');
      trashIcons.forEach(function(icon) {
        icon.addEventListener('click', function() {
          var parentContent = icon.closest('.history');
          if (parentContent) {
            // Show confirmation dialog
            var confirmDelete = confirm("Are you sure you want to delete this history?");
            if (confirmDelete) {
                // If user confirms, remove the history list
                parentContent.remove();
            }
          }
        });
      });
    });
