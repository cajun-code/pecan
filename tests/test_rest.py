from pecan import abort, expose, make_app, request, response
from pecan.rest import RestController
from webtest import TestApp
try:
    from simplejson import dumps, loads
except:
    from json import dumps, loads


class TestRestController(object):
    
    def test_basic_rest(self):
        
        class OthersController(object):
            
            @expose()
            def index(self):
                return 'OTHERS'
            
            @expose()
            def echo(self, value):
                return str(value)
        
        class ThingsController(RestController):
            data = ['zero', 'one', 'two', 'three']
            
            _custom_actions = {'count': ['GET'], 'length': ['GET', 'POST']}
            
            others = OthersController()
            
            @expose()
            def get_one(self, id):
                return self.data[int(id)]
            
            @expose('json')
            def get_all(self):
                return dict(items=self.data)
            
            @expose()
            def length(self, id, value=None):
                length = len(self.data[int(id)])
                if value:
                    length += len(value)
                return str(length)
            
            @expose()
            def get_count(self):
                return str(len(self.data))
            
            @expose()
            def new(self):
                return 'NEW'
            
            @expose()
            def post(self, value):
                self.data.append(value)
                response.status = 302
                return 'CREATED'
            
            @expose()
            def edit(self, id):
                return 'EDIT %s' % self.data[int(id)]
            
            @expose()
            def put(self, id, value):
                self.data[int(id)] = value
                return 'UPDATED'
            
            @expose()
            def get_delete(self, id):
                return 'DELETE %s' % self.data[int(id)]
            
            @expose()
            def delete(self, id):
                del self.data[int(id)]
                return 'DELETED'
            
            @expose()
            def reset(self):
                return 'RESET'
            
            @expose()
            def post_options(self):
                return 'OPTIONS'
            
            @expose()
            def options(self):
                abort(500)
            
            @expose()
            def other(self):
                abort(500)
        
        class RootController(object):
            things = ThingsController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test get_all
        r = app.get('/things')
        assert r.status_int == 200
        assert r.body == dumps(dict(items=ThingsController.data))
        
        # test get_one
        for i, value in enumerate(ThingsController.data):
            r = app.get('/things/%d' % i)
            assert r.status_int == 200
            assert r.body == value
        
        # test post
        r = app.post('/things', {'value':'four'})
        assert r.status_int == 302
        assert r.body == 'CREATED'
        
        # make sure it works
        r = app.get('/things/4')
        assert r.status_int == 200
        assert r.body == 'four'
        
        # test edit
        r = app.get('/things/3/edit')
        assert r.status_int == 200
        assert r.body == 'EDIT three'
        
        # test put
        r = app.put('/things/4', {'value':'FOUR'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/things/4')
        assert r.status_int == 200
        assert r.body == 'FOUR'
        
        # test put with _method parameter and GET
        r = app.get('/things/4?_method=put', {'value':'FOUR!'}, status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/things/4')
        assert r.status_int == 200
        assert r.body == 'FOUR'
        
        # test put with _method parameter and POST
        r = app.post('/things/4?_method=put', {'value':'FOUR!'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/things/4')
        assert r.status_int == 200
        assert r.body == 'FOUR!'
        
        # test get delete
        r = app.get('/things/4/delete')
        assert r.status_int == 200
        assert r.body == 'DELETE FOUR!'
        
        # test delete
        r = app.delete('/things/4')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/things')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 4
        
        # test delete with _method parameter and GET
        r = app.get('/things/3?_method=DELETE', status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/things')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 4
        
        # test delete with _method parameter and POST
        r = app.post('/things/3?_method=DELETE')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/things')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 3
        
        # test "RESET" custom action
        r = app.request('/things', method='RESET')
        assert r.status_int == 200
        assert r.body == 'RESET'
        
        # test "RESET" custom action with _method parameter
        r = app.get('/things?_method=RESET')
        assert r.status_int == 200
        assert r.body == 'RESET'
        
        # test the "OPTIONS" custom action
        r = app.request('/things', method='OPTIONS')
        assert r.status_int == 200
        assert r.body == 'OPTIONS'
        
        # test the "OPTIONS" custom action with the _method parameter
        r = app.post('/things', {'_method': 'OPTIONS'})
        assert r.status_int == 200
        assert r.body == 'OPTIONS'
        
        # test the "other" custom action
        r = app.request('/things/other', method='MISC', status=405)
        assert r.status_int == 405
        
        # test the "other" custom action with the _method parameter
        r = app.post('/things/other', {'_method': 'MISC'}, status=405)
        assert r.status_int == 405
        
        # test the "others" custom action
        r = app.request('/things/others/', method='MISC')
        assert r.status_int == 200
        assert r.body == 'OTHERS'

        # test the "others" custom action missing trailing slash
        r = app.request('/things/others', method='MISC', status=302)
        assert r.status_int == 302
        
        # test the "others" custom action with the _method parameter
        r = app.get('/things/others/?_method=MISC')
        assert r.status_int == 200
        assert r.body == 'OTHERS'
        
        # test an invalid custom action
        r = app.get('/things?_method=BAD', status=404)
        assert r.status_int == 404
        
        # test custom "GET" request "count"
        r = app.get('/things/count')
        assert r.status_int == 200
        assert r.body == '3'
        
        # test custom "GET" request "length"
        r = app.get('/things/1/length')
        assert r.status_int == 200
        assert r.body == str(len('one'))
        
        # test custom "GET" request through subcontroller
        r = app.get('/things/others/echo?value=test')
        assert r.status_int == 200
        assert r.body == 'test'
        
        # test custom "POST" request "length"
        r = app.post('/things/1/length', {'value':'test'})
        assert r.status_int == 200
        assert r.body == str(len('onetest'))
        
        # test custom "POST" request through subcontroller
        r = app.post('/things/others/echo', {'value':'test'})
        assert r.status_int == 200
        assert r.body == 'test'
    
    def test_nested_rest(self):
        
        class BarsController(RestController):
            
            data = [['zero-zero', 'zero-one'], ['one-zero', 'one-one']]
            
            @expose()
            def get_one(self, foo_id, id):
                return self.data[int(foo_id)][int(id)]
            
            @expose('json')
            def get_all(self, foo_id):
                return dict(items=self.data[int(foo_id)])
            
            @expose()
            def new(self, foo_id):
                return 'NEW FOR %s' % foo_id
            
            @expose()
            def post(self, foo_id, value):
                foo_id = int(foo_id)
                if len(self.data) < foo_id + 1:
                    self.data.extend([[]] * (foo_id - len(self.data) + 1))
                self.data[foo_id].append(value)
                response.status = 302
                return 'CREATED FOR %s' % foo_id
            
            @expose()
            def edit(self, foo_id, id):
                return 'EDIT %s' % self.data[int(foo_id)][int(id)]
            
            @expose()
            def put(self, foo_id, id, value):
                self.data[int(foo_id)][int(id)] = value
                return 'UPDATED'
            
            @expose()
            def get_delete(self, foo_id, id):
                return 'DELETE %s' % self.data[int(foo_id)][int(id)]
            
            @expose()
            def delete(self, foo_id, id):
                del self.data[int(foo_id)][int(id)]
                return 'DELETED'
        
        class FoosController(RestController):
            
            data = ['zero', 'one']
            
            bars = BarsController()
            
            @expose()
            def get_one(self, id):
                return self.data[int(id)]

            @expose('json')
            def get_all(self):
                return dict(items=self.data)
            
            @expose()
            def new(self):
                return 'NEW'
            
            @expose()
            def edit(self, id):
                return 'EDIT %s' % self.data[int(id)]
            
            @expose()
            def post(self, value):
                self.data.append(value)
                response.status = 302
                return 'CREATED'

            @expose()
            def put(self, id, value):
                self.data[int(id)] = value
                return 'UPDATED'
            
            @expose()
            def get_delete(self, id):
                return 'DELETE %s' % self.data[int(id)]
            
            @expose()
            def delete(self, id):
                del self.data[int(id)]
                return 'DELETED'
        
        class RootController(object):
            foos = FoosController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test get_all
        r = app.get('/foos')
        assert r.status_int == 200
        assert r.body == dumps(dict(items=FoosController.data))
        
        # test nested get_all
        r = app.get('/foos/1/bars')
        assert r.status_int == 200
        assert r.body == dumps(dict(items=BarsController.data[1]))
        
        # test get_one
        for i, value in enumerate(FoosController.data):
            r = app.get('/foos/%d' % i)
            assert r.status_int == 200
            assert r.body == value
        
        # test nested get_one
        for i, value in enumerate(FoosController.data):
            for j, value in enumerate(BarsController.data[i]):
                r = app.get('/foos/%s/bars/%s' % (i, j))
                assert r.status_int == 200
                assert r.body == value
        
        # test post
        r = app.post('/foos', {'value':'two'})
        assert r.status_int == 302
        assert r.body == 'CREATED'
        
        # make sure it works
        r = app.get('/foos/2')
        assert r.status_int == 200
        assert r.body == 'two'
        
        # test nested post
        r = app.post('/foos/2/bars', {'value':'two-zero'})
        assert r.status_int == 302
        assert r.body == 'CREATED FOR 2'
        
        # make sure it works
        r = app.get('/foos/2/bars/0')
        assert r.status_int == 200
        assert r.body == 'two-zero'
        
        # test edit
        r = app.get('/foos/1/edit')
        assert r.status_int == 200
        assert r.body == 'EDIT one'
        
        # test nested edit
        r = app.get('/foos/1/bars/1/edit')
        assert r.status_int == 200
        assert r.body == 'EDIT one-one'
        
        # test put
        r = app.put('/foos/2', {'value':'TWO'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/foos/2')
        assert r.status_int == 200
        assert r.body == 'TWO'
        
        # test nested put
        r = app.put('/foos/2/bars/0', {'value':'TWO-ZERO'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/foos/2/bars/0')
        assert r.status_int == 200
        assert r.body == 'TWO-ZERO'
        
        # test put with _method parameter and GET
        r = app.get('/foos/2?_method=put', {'value':'TWO!'}, status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/foos/2')
        assert r.status_int == 200
        assert r.body == 'TWO'
        
        # test nested put with _method parameter and GET
        r = app.get('/foos/2/bars/0?_method=put', {'value':'ZERO-TWO!'}, status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/foos/2/bars/0')
        assert r.status_int == 200
        assert r.body == 'TWO-ZERO'
        
        # test put with _method parameter and POST
        r = app.post('/foos/2?_method=put', {'value':'TWO!'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/foos/2')
        assert r.status_int == 200
        assert r.body == 'TWO!'
        
        # test nested put with _method parameter and POST
        r = app.post('/foos/2/bars/0?_method=put', {'value':'TWO-ZERO!'})
        assert r.status_int == 200
        assert r.body == 'UPDATED'
        
        # make sure it works
        r = app.get('/foos/2/bars/0')
        assert r.status_int == 200
        assert r.body == 'TWO-ZERO!'
        
        # test get delete
        r = app.get('/foos/2/delete')
        assert r.status_int == 200
        assert r.body == 'DELETE TWO!'
        
        # test nested get delete
        r = app.get('/foos/2/bars/0/delete')
        assert r.status_int == 200
        assert r.body == 'DELETE TWO-ZERO!'
        
        # test nested delete
        r = app.delete('/foos/2/bars/0')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/foos/2/bars')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 0
        
        # test delete
        r = app.delete('/foos/2')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/foos')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 2
        
        # test nested delete with _method parameter and GET
        r = app.get('/foos/1/bars/1?_method=DELETE', status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/foos/1/bars')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 2
        
        # test delete with _method parameter and GET
        r = app.get('/foos/1?_method=DELETE', status=405)
        assert r.status_int == 405
        
        # make sure it works
        r = app.get('/foos')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 2
        
        # test nested delete with _method parameter and POST
        r = app.post('/foos/1/bars/1?_method=DELETE')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/foos/1/bars')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 1
        
        # test delete with _method parameter and POST
        r = app.post('/foos/1?_method=DELETE')
        assert r.status_int == 200
        assert r.body == 'DELETED'
        
        # make sure it works
        r = app.get('/foos')
        assert r.status_int == 200
        assert len(loads(r.body)['items']) == 1

    def test_bad_rest(self):
        
        class ThingsController(RestController):
            pass
        
        class RootController(object):
            things = ThingsController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test get_all
        r = app.get('/things', status=404)
        assert r.status_int == 404
        
        # test get_one
        r = app.get('/things/1', status=404)
        assert r.status_int == 404
        
        # test post
        r = app.post('/things', {'value':'one'}, status=404)
        assert r.status_int == 404
        
        # test edit
        r = app.get('/things/1/edit', status=404)
        assert r.status_int == 404
        
        # test put
        r = app.put('/things/1', {'value':'ONE'}, status=404)
        
        # test put with _method parameter and GET
        r = app.get('/things/1?_method=put', {'value':'ONE!'}, status=405)
        assert r.status_int == 405
        
        # test put with _method parameter and POST
        r = app.post('/things/1?_method=put', {'value':'ONE!'}, status=404)
        assert r.status_int == 404
        
        # test get delete
        r = app.get('/things/1/delete', status=404)
        assert r.status_int == 404
        
        # test delete
        r = app.delete('/things/1', status=404)
        assert r.status_int == 404
        
        # test delete with _method parameter and GET
        r = app.get('/things/1?_method=DELETE', status=405)
        assert r.status_int == 405
        
        # test delete with _method parameter and POST
        r = app.post('/things/1?_method=DELETE', status=404)
        assert r.status_int == 404
        
        # test "RESET" custom action
        r = app.request('/things', method='RESET', status=404)
        assert r.status_int == 404
    
    def test_custom_delete(self):
        
        class OthersController(object):
            
            @expose()
            def index(self):
                return 'DELETE'
            
            @expose()
            def reset(self, id):
                return str(id)
        
        class ThingsController(RestController):
            
            others = OthersController()
            
            @expose()
            def delete_fail(self):
                abort(500)
        
        class RootController(object):
            things = ThingsController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test bad delete
        r = app.delete('/things/delete_fail', status=405)
        assert r.status_int == 405
        
        # test bad delete with _method parameter and GET
        r = app.get('/things/delete_fail?_method=delete', status=405)
        assert r.status_int == 405
        
        # test bad delete with _method parameter and POST
        r = app.post('/things/delete_fail', {'_method':'delete'}, status=405)
        assert r.status_int == 405
        
        # test custom delete without ID
        r = app.delete('/things/others/')
        assert r.status_int == 200
        assert r.body == 'DELETE'
        
        # test custom delete without ID with _method parameter and GET
        r = app.get('/things/others/?_method=delete', status=405)
        assert r.status_int == 405
        
        # test custom delete without ID with _method parameter and POST
        r = app.post('/things/others/', {'_method':'delete'})
        assert r.status_int == 200
        assert r.body == 'DELETE'
        
        # test custom delete with ID
        r = app.delete('/things/others/reset/1')
        assert r.status_int == 200
        assert r.body == '1'
        
        # test custom delete with ID with _method parameter and GET
        r = app.get('/things/others/reset/1?_method=delete', status=405)
        assert r.status_int == 405
        
        # test custom delete with ID with _method parameter and POST
        r = app.post('/things/others/reset/1', {'_method':'delete'})
        assert r.status_int == 200
        assert r.body == '1'
    
    def test_get_with_var_args(self):
        
        class OthersController(object):
            
            @expose()
            def index(self, one, two, three):
                return 'NESTED: %s, %s, %s' % (one, two, three)
        
        class ThingsController(RestController):
            
            others = OthersController()
            
            @expose()
            def get_one(self, *args):
                return ', '.join(args)
        
        class RootController(object):
            things = ThingsController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test get request
        r = app.get('/things/one/two/three')
        assert r.status_int == 200
        assert r.body == 'one, two, three'
        
        # test nested get request
        r = app.get('/things/one/two/three/others/')
        assert r.status_int == 200
        assert r.body == 'NESTED: one, two, three'
    
    def test_sub_nested_rest(self):
        
        class BazsController(RestController):
            
            data = [[['zero-zero-zero']]]
            
            @expose()
            def get_one(self, foo_id, bar_id, id):
                return self.data[int(foo_id)][int(bar_id)][int(id)]
        
        class BarsController(RestController):
            
            data = [['zero-zero']]
            
            bazs = BazsController()
            
            @expose()
            def get_one(self, foo_id, id):
                return self.data[int(foo_id)][int(id)]
        
        class FoosController(RestController):
            
            data = ['zero']
            
            bars = BarsController()
            
            @expose()
            def get_one(self, id):
                return self.data[int(id)]
        
        class RootController(object):
            foos = FoosController()
        
        # create the app
        app = TestApp(make_app(RootController()))
        
        # test sub-nested get_one
        r = app.get('/foos/0/bars/0/bazs/0')
        assert r.status_int == 200
        assert r.body == 'zero-zero-zero'
