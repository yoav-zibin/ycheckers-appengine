import webapp2
from PIL import Image, ImageOps, ImageDraw
from StringIO import StringIO
import datetime
import os
import urllib

# dev_appserver.py .
# http://localhost:8080/?winner=0&fbId0=10153589934097337&fbId1=10153693068502449&state=bKxbMxbMxbMxxbMxbMxbMxbMbMxbMxbMxbMxxxxxxxxxxxxxxxxxxwMxwMxwMxwMwMxwMxwMxwMxxwMxwMxwMxwM
# http://localhost:8080/fbId0=10153589934097337
# http://localhost:8080/?onlyBoard=t
# appcfg.py update .

class MainPage(webapp2.RequestHandler):

    def get(self):
        onlyBoard = self.request.get('onlyBoard') == "t"

        # Facebook recommends 1200 x 630 pixels for the og:image dimensions,
        # but I chose 952x500 (always keep this aspect-ratio! That ratio is assumed in the platform when showing the game-over "printscreen" for FB sharing.)
        img_w = 400 if onlyBoard else 952
        img_h = 400 if onlyBoard else 500
        # Board is 400x400, at center of img.
        board_w = 400
        board_h = 400
        board_x = (img_w - board_w)/2
        board_y = (img_h - board_h)/2
        cell_w = board_w/8 # 50x50
        cell_h = board_h/8
        avatar_w = cell_w * 4 / 5 #40x40
        avatar_h = cell_h * 4 / 5
        antialias_scale = 4 # Draw stuff 4-times bigger, and then scale down with ANTIALIAS to avoid rough circles.

        def loadImg(URL):
            file = StringIO(urllib.urlopen(URL).read())
            return Image.open(file)

        def getFbUrl(fbId, width, height):
            # http://graph.facebook.com/10153589934097337/picture?height=200&width=400
            # http://graph.facebook.com/10153693068502449/picture?height=200&width=400
            return "http://graph.facebook.com/" + fbId + "/picture?height=" + str(height) + "&width=" + str(width);

        def loadFbBigImg(fbId, width, height):
            if not fbId: return None
            big_img = loadImg(getFbUrl(fbId, width, height))
            return big_img.resize((width, height), Image.ANTIALIAS)

        def loadFbSmallImg(fbId):
            if not fbId: return None
            avatar = loadImg(getFbUrl(fbId, 50, 50))
            return avatar.resize((40, 40), Image.ANTIALIAS)

        def createCircle(color):
            size = (200, 200)
            img = Image.new('L', size, 0)
            draw = ImageDraw.Draw(img)
            start = 15
            end = 30
            draw.ellipse((start, start) + (200-start, 200-start), fill=color)
            draw.ellipse((end, end) + (200-end, 200-end), fill=0)
            return img.resize((50, 50), Image.ANTIALIAS)

        state=self.request.get('state')
        if not state: state = "bMxbMxbMxbMxxbMxbMxbMxbMbMxbMxbMxbMxxxxxxxxxxxxxxxxxxwMxwMxwMxwMwMxwMxwMxwMxxwMxwMxwMxwM"
        state = state.lower()
        winner=self.request.get('winner')
        # 0 is first player (black), 1 is second (white)
        fbIds=[self.request.get('fbId0'),self.request.get('fbId1')]
        fbSmallImgs=map(loadFbSmallImg, fbIds)
        fbBigImgs = [None, None]
        if fbIds[0] and fbIds[1]:
            for i in range(2):
                fbBigImgs[i] = loadFbBigImg(fbIds[i], img_w/2, img_h)
        elif fbIds[0] or fbIds[1]:
            for i in range(2):
                fbBigImgs[i] = loadFbBigImg(fbIds[i], img_w, img_h)

        black_king = fbSmallImgs[0] if fbIds[0] else Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-jpeg/black_king.jpeg'))
        black_man = fbSmallImgs[0] if fbIds[0] else Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-jpeg/black_man.jpeg'))
        white_king = fbSmallImgs[1] if fbIds[1] else Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-jpeg/white_king.jpeg'))
        white_man = fbSmallImgs[1] if fbIds[1] else Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-jpeg/white_man.jpeg'))
        board_img = Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-jpeg/board.jpeg'))
        if fbIds[0] or fbIds[1]: crown = Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-png/crown_small.png'))
        if winner: crown_big = Image.open(os.path.join(os.path.dirname(__file__), 'images/checkers-png/crown_big.png'))

        imgs={
            "white":{
                "man": white_man,
                "king": white_king,
            },
            "black":{
                "man": black_man,
                "king": black_king,
            }
        }

        # http://stackoverflow.com/questions/890051/how-do-i-generate-circular-thumbnails-with-pil
        size = (avatar_w * antialias_scale, avatar_h * antialias_scale)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((antialias_scale, antialias_scale) + ((avatar_w-1) * antialias_scale, (avatar_h-1) * antialias_scale), fill=255)
        mask = mask.resize((avatar_w, avatar_h), Image.ANTIALIAS)

        circle_mask = createCircle(255)
        white_circle = circle_mask
        black_circle = createCircle(1)

        composite_img = Image.new('RGB', (img_w,img_h), (255,255,255))
        if fbIds[0] and fbIds[1]:
            composite_img.paste(fbBigImgs[0],(0,0))
            composite_img.paste(fbBigImgs[1],(img_w/2,0))
        elif fbIds[0] or fbIds[1]:
            if fbIds[0]: composite_img.paste(fbBigImgs[0],(0,0))
            if fbIds[1]: composite_img.paste(fbBigImgs[1],(0,0))

        board_img_mask = None
        if fbIds[0] or fbIds[1]: board_img_mask = Image.new('L', (board_w, board_h), 204) # alpha is 204/255=0.8
        composite_img.paste(board_img, (board_x, board_y), board_img_mask)

        board=[]
        for row in range(8):
            board.append([])
            for col in range(8):
                board[row].append(None)

        pos = 0
        i = 0
        state_len = len(state)
        while i < state_len:
            color=state[i]
            i = i+1
            if color=="w":
                color="white"
            elif color=="b":
                color="black"
            elif color=="x":
                pos = pos+1
                continue
            else:
                raise Exception('Illegal color=' + color)

            piece=state[i]
            i = i+1
            if piece=="m":
                piece="man"
            elif piece=="k":
                piece="king"
            else:
                raise Exception('Illegal piece')
            row= 7 - pos/8 # Reversed the rows
            col = pos%8
            pos = pos+1
            board[row][col] = {"color": color, "piece": piece}

        for row in range(8):
            for col in range(8):
                if board[row][col]:
                    color_piece = board[row][col]
                    color = color_piece["color"]
                    piece = color_piece["piece"]
                    img = imgs[color][piece]
                    circle = white_circle if color == "white" else black_circle
                    x = board_x + col*cell_w
                    y = board_y + row*cell_h
                    composite_img.paste(img, (x+5,y+5), mask)
                    if fbIds[0 if color=="black" else 1]:
                        composite_img.paste(circle, (x,y), circle_mask)
                        # Maybe draw a crown
                        if piece == "king":
                            composite_img.paste(crown, (x+10,y-8), crown)

        if winner and fbIds[0] and fbIds[1]:
            # I can show the crown in the middle if there is just one fbId, but it looks "weird".
            # img_w/2 if not (fbIds[0] and fbIds[1]) else
            crown_big_w = 130
            crown_big_middle = img_w/4 if winner=="0" else img_w*3/4
            composite_img.paste(crown_big,(crown_big_middle - crown_big_w/2,0), crown_big)

        buf= StringIO()
        composite_img.save(buf, format= 'JPEG', quality=80) # default quality is 75, never go above 95
        png= buf.getvalue()

        self.response.headers['Content-Type'] = 'image/jpg'
        # Set forever cache headers (I copied what github.io returns); one year in the future.
        self.response.headers['Cache-Control'] = 'public,max-age=31556926'
        #self.response.headers['Age'] = '0'
        #self.response.headers["Last-Modified"] = 'Thu, 09 Jun 2016 13:41:32 GMT'
        # https://www.pythonanywhere.com/forums/topic/694/
        # If both Expires and max-age are set, max-age will take precedence. BUT: It is recommended that Expires should be set to a similar value.
        # 364 days in the future
        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(364)
        self.response.headers["Expires"] = expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")

        self.response.out.write(png)

app = webapp2.WSGIApplication([(r'/.*', MainPage),])
