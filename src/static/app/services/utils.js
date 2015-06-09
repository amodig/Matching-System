MatchingApp.service('Utils', function(){
  this.articlesToChartData = function(articles){
    var data = _.map(articles, function(article){
      return {
        value: Math.round(article.weight * 100),
        label: article.title,
        data: article
      }
    });

    return data;
  }

  this.topicsToHistoryData = function(topics){
    var weightSum = _.sum(topics, 'weight');

    console.log(weightSum);

    var data = _.map(topics, function(topic){
      return {
        keywordsToString: _(topic.keywords).map(function(keyword){ return keyword.content }).value().join(', '),
        portion: (topic.weight / weightSum) * 100 + '%'
      }
    });

    return data;
  }
});
