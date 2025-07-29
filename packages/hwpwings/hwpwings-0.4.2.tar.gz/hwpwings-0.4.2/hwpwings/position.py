class position():

    def save_pos(self):
        """
        현재 캐럿 위치의 좌표를 가져옵니다. 
        """
        return self.hwp.GetPos()

    def load_pos(self, save_pos:tuple):
        'save_pos에 저장된 좌표로 캐럿을 옮깁니다.'
        return self.hwp.SetPos(*save_pos)