MatchingApp.directive('cluster', function(EngineModels){
  var CLOUDSIZE = EngineModels.getCloudSize();

  var topics = [];
  var raphael, topicCloud, keywordCloud = null;

  function bindKeywords(keywords, onChange){
    raphael.set(_.map(keywords, function(keyword){ return keyword.handle }))
      .click(function(){

      })
      .hover(function(){
        this.parent.bringFront();
      })
      .dblclick(function(){
        var parent = this.parent;

        parent.removed = true;
        parent.remove({ animate: true });
      })
      .drag(
        function(dx, dy){
          dragMove(this, dx, dy);
        },
        function(){
          dragStart(this);
        },
        function(){
          var collision = false;
          var parent = this.parent;

          _.where(keywords, { removed: false }).forEach(function(keyword){
              if(parent != keyword && parent.collides(keyword)){
                collision = true;
              }
          });

          if(collision){
            parent.smoothMove(this.ox, this.oy, function(){
              onChange();
            });
          }else{
            onChange();
          }

          dragEnd(this);
        }
      );
  }

  function bindTopics(topics, onChange){
    raphael.set(_.map(topics, function(topic){ return topic.handle }))
    .click(function(){
      topics.forEach(function(topic){
        topic.setBorderColor(null);
      });

      var _this = this;

      var targetTopic = _.find(topics, { id: _this.parent.id });
      keywordCloud.setTitle('Drag keywords related to "' + targetTopic.content + '" here');
      keywordCloud.labelStartPoint = { x: targetTopic.dimensions().x, y: targetTopic.dimensions().y };
      keywordCloud.setLabels(targetTopic.keywords);

      this.parent.bringFront();

      bindKeywords(targetTopic.keywords, onChange);

      this.parent.setBorderColor('#337AB7');
    })
    .hover(function(){
      this.parent.bringFront();
    })
    .dblclick(function(){
      var parent = this.parent;

      parent.removed = true;
      parent.remove({ animate: true });

      keywordCloud.setLabels([]);
      keywordCloud.setTitle('Choose a topic to see its keywords');
    })
    .drag(
      function(dx, dy){
        dragMove(this, dx, dy);
      },
      function(){
        dragStart(this);
      },
      function(){
        var collision = false;
        var parent = this.parent;

        _.where(topics, { removed: false }).forEach(function(topic){
            if(parent != topic && parent.collides(topic)){
              collision = true;
            }
        });

        if(collision){
          parent.smoothMove(this.ox, this.oy, function(){
            onChange();
          });
        }else{
          onChange();
        }

        dragEnd(this);
      }
    );
  }

  function dragMove(el, dx, dy){
    var newX = el.ox + dx;
    var newY = el.oy + dy;

    var dim = el.parent.dimensions();
    var bounds = el.parent.inBounds(newX, newY)

    if(bounds.left){
      newX = ( el.parent.middle.x - CLOUDSIZE / 2 ) - dim.width / 2;
    }
    if(bounds.right){
      newX = el.parent.middle.x + CLOUDSIZE / 2 - dim.width / 2;
    }
    if(bounds.top){
      newY = ( el.parent.middle.y - CLOUDSIZE / 2 ) - dim.height / 2;
    }
    if(bounds.bottom){
      newY = el.parent.middle.y + CLOUDSIZE / 2 - dim.height / 2;
    }

    el.parent.move(newX, newY);
  }

  function dragStart(el){
    var pos = el.parent.dimensions();

    el.ox = pos.x;
    el.oy = pos.y;

    el.attr({ cursor: 'move' });

    el.parent.setOpacity(0.7);
  }

  function dragEnd(el){
    el.attr({ cursor: 'pointer' });
    el.parent.setOpacity(1);
  }

  function updateModel(scope){
    var formattedTopics = _.map(function(topic){
      var formattedKeywords = _.map(function(keyword){
        return { content: keyword.content, weight: keyword.weight, removed: keyword.removed };
      });

      return { content: topic.content, weight: topic.weight, removed: topic.removed, keywords: formattedKeywords };
    });

    scope.$apply(function(){
      scope.topics = formattedTopics;
    });
  }

  function initTopics(topicData, topicCloud, keywordCloud){
    topics = [];

    topicData.forEach(function(topic){
      var topicAttr = _.clone(topic);
      topicAttr.middle = topicCloud.middle;

      var topicLabel = EngineModels.createLabel(raphael, topicAttr);
      topicLabel.keywords = [];

      topic.keywords.forEach(function(keyword){
        var keywordAttr = _.clone(keyword);
        keywordAttr.middle = keywordCloud.middle;

        topicLabel.keywords.push(EngineModels.createLabel(raphael, keywordAttr));
      });

      topics.push(topicLabel);
    });
  }

  return {
    scope: {
      topics: '=ngModel'
    },
    template: '<div class="cluster-raphael"></div>',
    link: function(scope, elem, attrs){
      raphael = Raphael($(elem).children('.cluster-raphael')[0], CLOUDSIZE * 2, CLOUDSIZE);

      $(elem).addClass('cluster');

      topicCloud = EngineModels.createCloud(raphael, { middle: { x: 250, y: 250 } });
      keywordCloud = EngineModels.createCloud(raphael, { middle: { x: 850, y: 250 } });

      initTopics(scope.topics, topicCloud, keywordCloud);

      topicCloud.render();
      topicCloud.setTitle('Drag relevant topics here');
      keywordCloud.render();

      topicCloud.setLabels(topics);
      keywordCloud.setTitle('Drag keywords relevant to "' + topics[0].content + '" here');
      keywordCloud.labelStartPoint = { x: topics[0].dimensions().x, y: topics[0].dimensions().y };
      keywordCloud.setLabels(topics[0].keywords);


      bindTopics(topics, function(){ updateModel(scope) });
      bindKeywords(topics[0].keywords, function(){ updateModel(scope) });
    }
  }
});
