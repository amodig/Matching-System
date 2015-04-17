MatchingApp.controller('IterationController', function($scope, $rootScope, Api){
  $rootScope.activeLink = 'engine';

  Api.topics().success(function(topics){
    $scope.topics = topics;
  });

  $scope.next = function(){
    console.log($scope.topics);
  }
});
