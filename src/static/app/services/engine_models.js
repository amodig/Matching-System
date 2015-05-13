MatchingApp.service('EngineModels', function(){
  var CLOUDSIZE = 500;

  function rotateVector(vector, angle){
    return {
      x: vector.x * Math.cos(angle) - vector.y * Math.sin(angle),
      y: vector.x * Math.sin(angle) + vector.y * Math.cos(angle)
    };
  }

  function Cloud(raphael, attr){
    this.raphael = raphael;
    this.middle = attr.middle;
    this.labels = [];
    this.title = null;
    this.labelStartPoint = attr.labelStartPoint || { x: this.middle.x - CLOUDSIZE / 2, y: this.middle.y - CLOUDSIZE / 2 }
  }

  Cloud.prototype.setTitle = function(title){
    if(this.title){
      this.title.remove();
    }

    this.title = this.raphael.text(this.middle.x, this.middle.y, title).attr({ 'font-size': 20, 'fill': '#333', 'font-family': 'Helvetica, Arial, sans-serif' });
  }

  Cloud.prototype.render = function(){
    this.raphael.circle(this.middle.x, this.middle.y, 250).attr({ fill: '#EDEFF0', stroke: 'none' })
    this.raphael.circle(this.middle.x, this.middle.y, 180).attr({ fill: '#DCDFE2', stroke: 'none' });
    this.raphael.circle(this.middle.x, this.middle.y, 110).attr({ fill: '#CACED3', stroke: 'none' });
    this.raphael.circle(this.middle.x, this.middle.y, 40).attr({ fill: '#B8BEC4', stroke: 'none' });
  }

  Cloud.prototype.setLabels = function(labels){
    this.labels.forEach(function(label){
      label.remove({ animate: false });
    });

    this.labels = labels;

    var rotateAngle = 2 * Math.PI / labels.length;
    var unitVector = { x: 0, y: 1 };

    var cloud = this;

    _.where(this.labels, { removed: false }).forEach(function(label){
      label.render({ x: cloud.labelStartPoint.x, y: cloud.labelStartPoint.y });

      var dim = label.dimensions();
      var distanceToMiddle = label.distanceTo(cloud.middle.x, cloud.middle.y);
      var vectorWidth = (1 - label.weight) * (CLOUDSIZE / 2);

      var positionVector = {
        x: cloud.middle.x + unitVector.x * vectorWidth,
        y: cloud.middle.y + unitVector.y * vectorWidth
      };

      label.smoothMove(positionVector.x - dim.width / 2, positionVector.y - dim.height / 2);
      label.setWeight(label.weight);

      unitVector = rotateVector(unitVector, rotateAngle);
    });
  }

  function Label(raphael, attr){
    this.PADDING = 6;
    this.BG_COLOR = '#485563';

    this.raphael = raphael;
    this.content = attr.content;
    this.weight = attr.weight;
    this.middle = attr.middle;
    this.id = _.uniqueId();
    this.removed = false;
  }

  Label.prototype.inBounds = function(newX, newY){
    var dim = this.dimensions();

    var middle = {
      x: newX + dim.width / 2,
      y: newY + dim.height / 2
    };

    var leftBound = middle.x < this.middle.x - CLOUDSIZE / 2;
    var rightBound = middle.x > this.middle.x + CLOUDSIZE / 2;
    var topBound = middle.y < this.middle.y - CLOUDSIZE / 2;
    var bottomBound = middle.y > this.middle.y + CLOUDSIZE / 2;

    return {
      left: leftBound,
      right: rightBound,
      top: topBound,
      bottom: bottomBound
    };
  }

  Label.prototype.bringFront = function(){
    this.background.toFront();
    this.text.toFront();
    this.handle.toFront();
  }

  Label.prototype.render = function(options){
    this.removed = false;
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

  Label.prototype.collides = function(keyword){
    var me = this.handle.getBBox();
    var target = keyword.handle.getBBox();

    return !(target.x > me.x + me.width ||
           target.x + target.width < me.x ||
           target.y > me.y + me.height ||
           target.y + target.height < me.y);
  }

  Label.prototype.setBgColor = function(color){
    this.background.attr({ fill: color });
  }

  Label.prototype.setOpacity = function(opacity){
    this.text.animate({ opacity: opacity }, 300);
    this.background.animate({ opacity: opacity }, 300);
  }

  Label.prototype.setFontColor = function(color){
    this.text.attr({ fill: color });
  }

  Label.prototype.setWeight = function(weight){
    var color = tinycolor(this.BG_COLOR);

    this.weight = weight;

    var distanceToMiddle = this.distanceTo(this.middle.x, this.middle.y);

    var lightness = Math.round(50 * this.weight + 50);

    this.setBgColor(color.lighten(100 - lightness));

    if(this.weight < 0.3){
      this.setFontColor('#333');
    }else{
      this.setFontColor('white');
    }
  }

  Label.prototype.distanceTo = function(x, y){
    var dim = this.dimensions();

    var middle = {
      x: dim.x + dim.width / 2,
      y: dim.y + dim.height / 2
    };

    var distanceX = Math.abs(x - middle.x);
    var distanceY = Math.abs(y - middle.y);

    return Math.sqrt(Math.pow(distanceX, 2) + Math.pow(distanceY, 2));
  }

  Label.prototype.remove = function(options){
    if(options.animate){
      this.text.animate({ opacity: 0 }, 300, '<', function(){
        this.remove();
      });

      this.background.animate({ opacity: 0 }, 300, '<', function(){
        this.remove();
      });
    }else{
      this.text.remove();
      this.background.remove();
    }

    this.handle.remove();
  }

  Label.prototype.smoothMove = function(x, y, callback){
    var _this = this;
    var textDim = this.text.getBBox();

    this.background.animate({ x: x, y: y }, 300, '<');

    this.handle.animate({ x: x, y: y }, 300, '<', function(){
      var distanceToMiddle = _this.distanceTo(_this.middle.x, _this.middle.y);

      _this.setWeight(Math.max(0, 1 - distanceToMiddle / (CLOUDSIZE / 2)));

      if($.isFunction(callback)){
        callback();
      };
    });

    this.text.animate({ x: textDim.width / 2 + x + this.PADDING, y: textDim.height / 2 + y + this.PADDING }, 300, '<');

    this.bringFront();
  }

  Label.prototype.move = function(x, y){
    var textDim = this.text.getBBox();

    this.background.attr({ x: x, y: y });
    this.handle.attr({ x: x, y: y });
    this.text.attr({ x: textDim.width / 2 + x + this.PADDING, y: textDim.height / 2 + y + this.PADDING });

    var distanceToMiddle = this.distanceTo(this.middle.x, this.middle.y);

    this.setWeight(Math.max(0, 1 - distanceToMiddle / (CLOUDSIZE / 2)));

    this.bringFront();
  }

  Label.prototype.setBorderColor = function(color){
    if(!color){
      this.background.attr({ 'stroke': 'none' });
    }else{
      this.background.attr({ 'stroke-width': '3' });
      this.background.attr({ 'stroke': color });
    }
  }

  Label.prototype.dimensions = function(){
    var dim = this.handle.getBBox();

    return {
      x: this.handle.attr('x'),
      y: this.handle.attr('y'),
      width: dim.width,
      height: dim.height
    };
  }

  this.getCloudSize = function(){
    return CLOUDSIZE;
  }

  this.createLabel = function(raphael, attr){
    return new Label(raphael, attr);
  }

  this.createCloud = function(raphael, attr){
    return new Cloud(raphael, attr);
  }

});
