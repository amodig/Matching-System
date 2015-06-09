MatchingApp.controller('IterationController', function($scope, $rootScope, Api, Utils){
  $rootScope.activeLink = 'engine';

  $scope.iterationHistory = [];
  $scope.currentIteration = 1;

  function fetchTopics(){
    $scope.loading = true;

    Api.topics().success(function(topics){
      $scope.topics = topics;
      $scope.loading = false;
    });
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
    $scope.relatedArticles = Utils.articlesToChartData(topic.relatedArticles);
    $scope.chosenArticle = _.max(topic.relatedArticles, 'weight');

    topic.selected = true;
  }

  $scope.chooseArticle = function(article){
    $scope.chosenArticle = article;
  }

  $scope.toggleHistory = function(){
    $scope.showHistory = !$scope.showHistory;
  }

  $scope.next = function(){
    var mostWeight = _($scope.topics).sortBy('-weight').take(3).value();
    var historyTopics = Utils.topicsToHistoryData(mostWeight);

    $scope.iterationHistory.push({
      iteration: $scope.currentIteration,
      topics: historyTopics
    });

    $scope.currentIteration++;

    console.log($scope.iterationHistory);

    fetchTopics();
  }
});
