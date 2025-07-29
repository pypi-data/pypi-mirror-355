def xxx( e ) :
    equation = e
    def Clean(eq):
#        CleanedEq=eq
        CEq=""
        for i in range(len(eq)):
            if eq[i] not in "0123456789+-*/%.":
                continue
            else:
                CEq+=eq[i]
        return CEq

        

    #TO DEL 'UP' hear
    """
    the 1.1.2 version plan:
    1=clean the equation
    2=make the mince working "like -1+2"
    3=make the spaces not problem "like - 2+ 3    *4"

    the 1.0.1 version plan:
    1=read the equation
    2=slice if to symboles and numbers
    3=do the first calc */%
    4=do the last calc +-
    5=return the result
    """
    #data
    NL = []
    SL = []
    DNL= [] #deleted numbers list
    DSL= [] #deleted symboles List

    def GSI( eq ) :
        for i in range( len( eq ) ) :
            if eq[ i ] in "+-*/%" :
                return i
        return False
    def GFN( eq ) :
            return eq[ : GSI( eq ) ]
    def DFN( eq ) :
            return eq[ GSI( eq ) : ]
    def GS( eq ) :
            return eq[ GSI( eq ) ]
    def DS( eq ) :
            return eq[ GSI( eq ) +1 : ]
    def SSexistingTST( eq ) :#special symboles existing tst
            ss = 0
            for i in range( len( eq ) ) :
                if eq[ i ] in "*/%" :
                    ss += 1
            if ss > 0 :
                return True
            else :
                return False
    def NSonlyTST( eq ) :#NORMAL SYMBOLES ONLY - TEST
            ns = 0
            for i in range( len( eq ) ) :
                if eq[ i ] in "+-" :
                    ns += 1
            if ns > 0 :
                return True
            else :
                return False
    def FixTheMins(NL,SL):
         for i in range(len(SL)-1):
              if NL[i] == "":
                   NL[i]="0"
    e=Clean(e)
    NL.append( GFN( e ) )
    e = DFN( e )
    while e :
            SL.append( GS( e ) )
            e = DS( e )
            if GSI( e ) is False :
                NL.append( e )
                e = DFN( e )
                break
            NL.append( GFN( e ) )
            e = DFN( e )
    FixTheMins(NL,SL)
    TOURNUMBER=1
    while len( SL ) > 0 and SSexistingTST(SL):
        i = GSI( SL )
        while SL[i] not in "*/%":
            DSL.append(SL[i])
            SL.pop(i)
            DNL.append(NL[i])
            NL.pop(i)
            i = GSI( SL )
        if SL[ i ] == "*" :
            NL[ i ] = float( NL[ i ] ) * float( NL[ i + 1 ] )
            NL.pop( i + 1 )
            SL.pop( i )
        elif SL[ i ] == "/" :
            NL[ i ] = float( NL[ i ] ) / float( NL[ i + 1 ] )
            NL.pop( i + 1 )
            SL.pop( i )
        elif SL[ i ] == "%" :
            NL[ i ] = float( NL[ i ] ) % float( NL[ i + 1 ] )
            NL.pop(  i + 1  )
            SL.pop(  i  )
        TOURNUMBER+=1
    TOURNUMBER=1
    DSL+=SL
    DNL+=NL
    NL.clear()
    SL.clear()
    SL+=DSL
    NL+=DNL
    while len( SL ) > 0 and NSonlyTST( SL ) :
        i = GSI( SL )
        if SL[ i ] == "+" :
            NL[ i ] = float( NL[ i ] ) + float( NL[ i + 1 ] )
            NL.pop( i + 1 )
            SL.pop( i )
        elif SL[ i ] == "-" :
            NL[ i ] = float( NL[ i ] ) - float( NL[ i + 1 ] )
            NL.pop(  i + 1  )
            SL.pop(  i  )
        TOURNUMBER+=1
    RESULT = NL[ 0 ]
    return RESULT
e="850*2000-300*0-1+400/70"
q=850*2000-300*-1+400/70
print(f'{e}={xxx(e)}={q}{"="*20}{q==xxx(e)}')