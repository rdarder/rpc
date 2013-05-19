(function () {
  var app = angular.module('app', ['rpc']);
  app.run([ '$location', '$rootScope', 'rpc', 'rpc_watch',
    function (location, rootScope, rpc, rpc_watch) {
      rootScope.rpc = rpc.init('/rpc');
      rootScope.rpc_watch = rpc_watch('rpc');
    }
  ]);

  app.controller('main', [
    '$scope', function (self) {
      self.a = 10;
      self.b = 15;
      self.rpc_watch('math.fast_add', 'a', 'b').into('result');

      self.rpc('db.list_tables').then(function (tables) {
        self.table_list = tables
      });
      self.rpc_watch('db.get_create', 'table').into('table_create');
      self.rpc_watch('db.get_all_rows', 'table').into('table_data');
    }
  ]);

}());
