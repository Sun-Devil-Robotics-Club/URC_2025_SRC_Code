import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
import cv2
import numpy as numpy

from sensor_msgs.msg import Image


class ImageSubscriber(Node):
    def __init__(self):
        super().__init__('image_collect_node')
        self.image_subscriber = self.create_subscription(Image,'/zed2/zed_node/rgb_raw/image_raw_color',self.listener_callback,10)
        self.timer = self.create_timer(2, self.timer_callback)
        self.path = "/home/pknadimp/sdrc_ws/src/sdrc_zed2/sdrc_zed2/images/post3/post3_"    
        self.br = CvBridge()
        self.i = 0


    def listener_callback(self,img):
        self.image  = self.br.imgmsg_to_cv2(img)
        cv2.imshow("image",self.image)
        cv2.waitKey(1)

    def timer_callback(self):
        if self.i<100:
            path = self.path+str(self.i)+".png"
            print(path)
            cv2.imwrite(path,self.image)
            self.i = self.i+1
      
def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()