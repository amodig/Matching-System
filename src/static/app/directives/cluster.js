MatchingApp.directive('cluster', function(){
  var WIDTH = 500;
  var HEIGHT = 500;

  function rotateVector(vector, angle){
    return {
      x: vector.x * Math.cos(angle) - vector.y * Math.sin(angle),
      y: vector.x * Math.sin(angle) + vector.y * Math.cos(angle)
    };
  }

  function initBackground(raphael){
    raphael.circle(WIDTH / 2, HEIGHT / 2, 250).attr({ fill: '#EDEFF0', stroke: 'none' })
    raphael.circle(WIDTH / 2, HEIGHT / 2, 180).attr({ fill: '#DCDFE2', stroke: 'none' });
    raphael.circle(WIDTH / 2, HEIGHT / 2, 110).attr({ fill: '#CACED3', stroke: 'none' });
    raphael.circle(WIDTH / 2, HEIGHT / 2, 40).attr({ fill: '#B8BEC4', stroke: 'none' });
  }

  function initKeywords(keywords){
    var rotateAngle = 2 * Math.PI / keywords.length;
    var unitVector = { x: 0, y: 1 };

    keywords.forEach(function(keyword){
      var dim = keyword.dimensions();
      var distanceToMiddle = keyword.distanceTo(WIDTH / 2, HEIGHT / 2);
      var vectorWidth = (1 - keyword.weight) * (WIDTH / 2);

      var positionVector = {
        x: WIDTH / 2 + unitVector.x * vectorWidth,
        y: HEIGHT / 2 + unitVector.y * vectorWidth
      };

      keyword.smoothMove(positionVector.x - dim.width / 2, positionVector.y - dim.height / 2);
      keyword.setWeight(keyword.weight);

      unitVector = rotateVector(unitVector, rotateAngle);
    });
  }

  function Topic(raphael, attr){
    this.raphael = raphael;
    this.content = attr.content;
    this.weight = attr.weight;
  }

  Topic.prototype.render = function(options){
    this.handle = this.raphael.text(options.x, options.y, this.content).attr({ 'font-size': 24, 'fill': '#333', 'font-family': 'Helvetica, Arial, sans-serif', 'cursor': 'pointer' });
  }

  function Keyword(raphael, attr){
    this.PADDING = 6;
    this.BG_COLOR = '#485563';

    this.raphael = raphael;
    this.content = attr.content;
    this.weight = attr.weight;
  }

  Keyword.prototype.bringFront = function(){
    this.background.toFront();
    this.text.toFront();
    this.handle.toFront();
  }

  Keyword.prototype.render = function(options){
    this.text = this.raphael.text(0, 0, this.content).attr({ 'font-size' : 14, 'fill': 'white', 'font-family': 'Helvetica, Arial, sans-serif' });
    var textDim = this.text.getBBox();

    this.background = this.raphael.rect(options.x, options.y, this.PADDING * 2 + textDim.width, this.PADDING * 2 + textDim.height, 4).attr({ 'fill': this.BG_COLOR, 'stroke': 'none' });
    var backgroundDim = this.background.getBBox();

    this.text.attr({ x: textDim.width / 2 + backgroundDim.x + this.PADDING, y: textDim.height / 2 + backgroundDim.y + this.PADDING });

    this.handle = this.background.clone();
    this.handle.attr({ fill: 'rgba(0,0,0,.0)', stroke: 'none', cursor: 'pointer' });
    this.handle.parent = this;

    this.bringFront();
  }

  Keyword.prototype.collides = function(keyword){
    var me = this.handle.getBBox();
    var target = keyword.handle.getBBox();

    return !(target.x > me.x + me.width ||
           target.x + target.width < me.x ||
           target.y > me.y + me.height ||
           target.y + target.height < me.y);
  }

  Keyword.prototype.setBgColor = function(color){
    this.background.attr({ fill: color });
  }

  Keyword.prototype.setFontColor = function(color){
    this.text.attr({ fill: color });
  }

  Keyword.prototype.setWeight = function(weight){
    var color = tinycolor(this.BG_COLOR);

    this.weight = weight;

    var distanceToMiddle = this.distanceTo(WIDTH / 2, HEIGHT / 2);

    var lightness = Math.round(50 * this.weight + 50);

    this.setBgColor(color.lighten(100 - lightness));

    if(this.weight < 0.3){
      this.setFontColor('#333');
    }else{
      this.setFontColor('white');
    }
  }

  Keyword.prototype.distanceTo = function(x, y){
    var dim = this.dimensions();

    var middle = {
      x: dim.x + dim.width / 2,
      y: dim.y + dim.height / 2
    };

    var distanceX = Math.abs(x - middle.x);
    var distanceY = Math.abs(y - middle.y);

    return Math.sqrt(Math.pow(distanceX, 2) + Math.pow(distanceY, 2));
  }

  Keyword.prototype.remove = function(callback){
    this.text.animate({ opacity: 0 }, 300, '<', function(){
      this.remove();
    });

    this.background.animate({ opacity: 0 }, 300, '<', function(){
      this.remove();

      if($.isFunction(callback)){
        callback();
      }
    });

    this.handle.remove();
  }

  Keyword.prototype.smoothMove = function(x, y){
    var _this = this;
    var textDim = this.text.getBBox();

    this.background.animate({ x: x, y: y }, 300, '<');

    this.handle.animate({ x: x, y: y }, 300, '<', function(){
      var distanceToMiddle = _this.distanceTo(WIDTH / 2, HEIGHT / 2);

      _this.setWeight(Math.max(0, 1 - distanceToMiddle / (WIDTH / 2)));
    });

    this.text.animate({ x: textDim.width / 2 + x + this.PADDING, y: textDim.height / 2 + y + this.PADDING }, 300, '<');

    this.bringFront();
  }

  Keyword.prototype.move = function(x, y){
    var textDim = this.text.getBBox();

    this.background.attr({ x: x, y: y });
    this.handle.attr({ x: x, y: y });
    this.text.attr({ x: textDim.width / 2 + x + this.PADDING, y: textDim.height / 2 + y + this.PADDING });

    var distanceToMiddle = this.distanceTo(WIDTH / 2, HEIGHT / 2);

    this.setWeight(Math.max(0, 1 - distanceToMiddle / (WIDTH / 2)));

    this.bringFront();
  }

  Keyword.prototype.dimensions = function(){
    var dim = this.handle.getBBox();

    return {
      x: this.handle.attr('x'),
      y: this.handle.attr('y'),
      width: dim.width,
      height: dim.height
    };
  }

  return {
    scope: {
      cluster: '=ngModel'
    },
    template: '<h2 class="text-center">{[cluster.topic.content]}</h2><div class="cluster-raphael"></div>',
    link: function(scope, elem, attrs){
      var topic = {};
      var keywords = [];
      var raphael = Raphael($(elem).children('.cluster-raphael')[0], WIDTH, HEIGHT);

      $(elem).addClass('cluster');

      initBackground(raphael);

      topic = new Topic(raphael, { content: 'Lorem ipsum dolor sit amet', weight: 0.9 });
      topic.render({ x: WIDTH / 2, y: HEIGHT / 2 });

      topic.handle
        .dblclick(function(){
          if(confirm('Are you sure you want to remove the whole topic?')){
            keywords.forEach(function(keyword){
              keyword.remove();
            });

            $(elem).addClass('removed');

            keywords = [];
          }
        });

      for(var i=0; i<8; i++){
        var keyword = new Keyword(raphael, { content: 'Lorem ipsum', weight: Math.random() });
        keyword.render({ x: 0, y: 0 });
        keywords.push(keyword)
      }

      initKeywords(keywords);

      raphael.set(_.map(keywords, function(keyword){ return keyword.handle }))
        .hover(function(){
          this.parent.bringFront();
        })
        .dblclick(function(){
          var parent = this.parent;

          parent.remove(function(){
            keywords = _.filter(keywords, function(keyword){ return keyword != parent });
          });
        })
        .drag(
          function(dx, dy){
            var newX = this.ox + dx;
            var newY = this.oy + dy;

            var dim = this.parent.dimensions();

            var middle = {
              x: newX + dim.width / 2,
              y: newY + dim.height / 2
            };

            var leftBound = middle.x < 0;
            var rightBound = middle.x > WIDTH;
            var topBound = middle.y < 0;
            var bottomBound = middle.y > HEIGHT;

            if(leftBound){
              newX = -(dim.width / 2);
            }
            if(rightBound){
              newX = WIDTH - dim.width / 2;
            }
            if(topBound){
              newY = -(dim.height / 2);
            }
            if(bottomBound){
              newY = HEIGHT - dim.height / 2;
            }

            this.parent.move(newX, newY);
          },
          function(){
            var pos = this.parent.dimensions();

            this.ox = pos.x;
            this.oy = pos.y;

            this.attr({ cursor: 'move' });
          },
          function(){
            var collision = false;
            var parent = this.parent;

            keywords.forEach(function(keyword){
                if(parent != keyword && parent.collides(keyword)){
                  collision = true;
                }
            });

            if(collision){
              parent.smoothMove(this.ox, this.oy);
            }

            this.attr({ cursor: 'pointer' });
          }
        )
    }
  }
});
