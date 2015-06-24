MatchingApp.controller('SearchController', function($scope, $rootScope, $location){
  $rootScope.activeLink = 'engine';

  $scope.search = function(){
    $location.path('engine/topics/' + $scope.keyword);
  }
});
