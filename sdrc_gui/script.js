// ROS Connection and Image Listener
var ros = new ROSLIB.Ros({
  url: "ws://localhost:9090",
});

ros.on("connection", function () {
  console.log("Connected to websocket server.");
});


ros.on("error", function (error) {
  console.error("ROS Connection Error: ", error);
});

ros.on("close", function () {
  console.warn("ROS Connection Closed.");
});

// ---- Camera Listener (existing) ----
var imageListener = new ROSLIB.Topic({
  ros: ros,
  name: "/camera/image_base64",
  messageType: "std_msgs/String",
});

imageListener.subscribe(function (message) {
  var imageElement = document.getElementById("camera-image");
  imageElement.src = "data:image/jpeg;base64," + message.data;
});

// ---- LED Button Functionality (existing) ----
var LEDStatus = false;
var ledService = new ROSLIB.Service({
  ros: ros,
  name: "/set_led",
  serviceType: "sdrc_interfaces/srv/SetLed",
});

function onLEDButtonClick() {
  LEDStatus = !LEDStatus;
  var button = document.getElementById("LEDButton");
  if (LEDStatus) {
    button.innerHTML = "Change LED Status <br>Current Status: On";
    button.style.color = "green";

    // Example: call the SetLed service
    var request = new ROSLIB.ServiceRequest({
      color: "blue" // or "red", etc.
    });
    ledService.callService(request, function(result) {
      console.log("LED service response: ", result.success);
    });

  } else {
    button.innerHTML = "Change LED Status<br/> Current Status: Off";
    button.style.color = "red";

    // Turn LED off or some other color
    var requestOff = new ROSLIB.ServiceRequest({
      color: "off"
    });
    ledService.callService(requestOff, function(result) {
      console.log("LED off response: ", result.success);
    });
  }
}

// ---- Teleop: Publish /cmd_vel commands ----
var cmdVelPub = new ROSLIB.Topic({
  ros: ros,
  name: "/cmd_vel",
  messageType: "geometry_msgs/Twist"
});

// function to send velocity
function sendVelocity(linearX, angularZ) {
  var twist = new ROSLIB.Message({
    linear: { x: linearX, y: 0.0, z: 0.0 },
    angular: { x: 0.0, y: 0.0, z: angularZ }
  });
  cmdVelPub.publish(twist);
  console.log("Sent cmd_vel:", twist);
}

// ---- Waypoint / GNSS Input ----
var waypointPub = new ROSLIB.Topic({
  ros: ros,
  name: "/latlon_waypoint",
  messageType: "std_msgs/String"
  // or geometry_msgs/PoseStamped if you prefer
});

function sendWaypoint() {
  var latVal = document.getElementById("latInput").value;
  var lonVal = document.getElementById("lonInput").value;
  var msgStr = latVal + "," + lonVal; // e.g. "35.0,-120.0"
  var waypointMsg = new ROSLIB.Message({
    data: msgStr
  });
  waypointPub.publish(waypointMsg);
  console.log("Published waypoint:", msgStr);
}

// ---- Battery Subscriber Example ----
var batterySub = new ROSLIB.Topic({
  ros: ros,
  name: "/battery",
  messageType: "std_msgs/Float32"
});

batterySub.subscribe(function(msg) {
  var batterySpan = document.getElementById("batteryVal");
  batterySpan.innerHTML = msg.data.toFixed(2) + " V";
});

// ---- On DOM Loaded ----
document.addEventListener("DOMContentLoaded", () => {
  var ledButton = document.getElementById("LEDButton");
  ledButton.addEventListener("click", onLEDButtonClick);

  console.log("Web UI fully loaded and ready.");
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

    }};
