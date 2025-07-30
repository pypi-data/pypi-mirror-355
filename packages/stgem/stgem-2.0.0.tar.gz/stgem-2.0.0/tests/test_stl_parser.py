from stgem.monitor.stl import STLRobustness


def test_stl_parser():
    r = STLRobustness("x>0")
    r = STLRobustness("x>0 and y>10")
    r = STLRobustness("x>0 and y>10 and z>10")
    r = STLRobustness("(x>0) and y>10 and z>10")
    r = STLRobustness("(x>0 and (y>10 and (z>10)))")
    r = STLRobustness("not(x>0 and y<10)")
    r = STLRobustness("not(not(x>0 and y<10))")
    r = STLRobustness("x>0 or y<0")
    r = STLRobustness("(x>0) or (y<0)")

    r = STLRobustness("always[0,10](SPEED < 100) or eventually[0,20](3000 < RPM)")
    
    r = STLRobustness("(THROTTLE < 8.8) and (eventually[0,20](THROTTLE > 40.0))")

    f1 = """"
        always[11,50](
          (
           (THROTTLE < 8.8) and (eventually[0,0.05](THROTTLE > 40.0)) or 
           (THROTTLE > 40.0) and (eventually[0,0.05](THROTTLE < 8.8))
          ) -> always[1,5](|MU| < 0.008)
         )
      """
    r = STLRobustness(f1)

    f2 = """
    always[0,30]( 
      ( GEAR != 5 and (eventually[0.001,0.1](GEAR == 5)) ) -> 
      ( eventually[0.001,0.1]( always[0,2.5](GEAR == 5) ) 
    ) 
    """
    r = STLRobustness(f2)
