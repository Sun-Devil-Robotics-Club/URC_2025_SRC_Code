// ROS Connection and Image Listener
var ros = new ROSLIB.Ros({
  url: "ws://localhost:9090",
});

ros.on("connection", function () {
  console.log("Connected to websocket server.");
});

var imageListener = new ROSLIB.Topic({
  ros: ros,
  name: "/camera/image_base64",
  messageType: "std_msgs/String",
});

imageListener.subscribe(function (message) {
  var imageElement = document.getElementById("camera-image");
  imageElement.src = "data:image/jpeg;base64," + message.data;
});

// LED Button Functionality
var button;
var LEDStatus = false;

document.addEventListener("DOMContentLoaded", (event) => {
  button = document.getElementById("LEDButton");
  button.addEventListener("click", onButtonClicked);
});

function onButtonClicked() {
  LEDStatus = !LEDStatus;
  if (LEDStatus) {
    button.innerHTML = "Change LED Status <br>Current Status: On";
    button.style.color = "green";
  } else {
    button.innerHTML = "Change LED Status<br/> Current Status: Off";
    button.style.color = "red";
  }
}
