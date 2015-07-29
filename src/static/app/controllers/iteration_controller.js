MatchingApp.controller('IterationController', function($scope, $rootScope, $routeParams, $location, Api, Utils){
  $rootScope.activeLink = 'engine';

  $scope.keyword = $routeParams.keyword;
  $scope.iterationHistory = [];
  $scope.currentIteration = 1;

  function fetchTopics(){
    $scope.chosenArticle = null;
    $scope.relatedArticles = null;
    $scope.loading = true;

    if($scope.currentIteration == 1){
      Api.topics($scope.keyword).success(function(topics){
        $scope.topics = topics.topics;
        $scope.loading = false;
      });
    }else{
      var feedback = _.map($scope.topics, function(topic){ return { text: parseInt(topic.id), weight: topic.weight } });

      Api.next(feedback).success(function(topics){
        $scope.topics = topics.topics;
        $scope.loading = false;
      });
    }
  }

  fetchTopics();

  $scope.unchooseTopics = function(){
    $scope.topics.forEach(function(topic){
      topic.selected = false;
    });

    $scope.relatedArticles = null;
    $scope.chosenArticle = null;
  }

  $scope.chooseTopic = function(topic){
    $scope.unchooseTopics();

    if(topic.relatedArticles){
      $scope.relatedArticles = Utils.articlesToChartData(topic.relatedArticles);
    }else{
      Api.getTopicRelatedArticles(topic.id).success(function(articles){
        topic.relatedArticles = articles.articles;
        $scope.relatedArticles = Utils.articlesToChartData(topic.relatedArticles);
      });
    }

    topic.selected = true;
  }

  $scope.chooseArticle = function(article){
    $scope.chosenArticle = article;
  }

  $scope.toggleHistory = function(){
    $scope.showHistory = !$scope.showHistory;
  }

  $scope.newSearch = function(){
    if(confirm('Are you sure you want to start a new search?')){
      $location.path('engine/search');
    }
  }

  $scope.next = function(){
    var mostWeight = _($scope.topics).sortBy('-weight').take(3).value();
    var historyTopics = Utils.topicsToHistoryData(mostWeight);

    $scope.iterationHistory.push({
      iteration: $scope.currentIteration,
      topics: historyTopics
    });

    $scope.currentIteration++;

    fetchTopics();
  }
});
