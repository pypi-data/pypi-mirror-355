from PyQt5.QtWidgets import QMdiSubWindow, QMdiArea
from PyQt5.QtCore import Qt, QRect
from .debug_util import debug_print, error_print

STICKY_DIST = 20  # Sticky動作の距離閾値（ピクセル）
HYSTERESIS = 10   # ヒステリシス（ピクセル）

class StickyMdiSubWindow(QMdiSubWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dragging = False
        self._resizing = False
        self._drag_start_pos = None
        self._resize_start_rect = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            resize_dir = self.isInResizeArea(event.pos())
            if resize_dir:
                self._resizing = True
                self._resize_dir = resize_dir
                self._resize_start_rect = self.geometry()
                self._drag_start_pos = event.globalPos()
                self._resize_adjacent_all = self.findAllAdjacentWindows(resize_dir)
            else:
                self._dragging = True
                self._drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def findAllAdjacentWindows(self, resize_dir):
        mdi_area = self.getMdiArea()
        if mdi_area is None:
            return []
        checked = set()
        result = []
        def dfs(win, dir):
            checked.add((win, dir))
            my_rect = win.geometry()
            for other in mdi_area.subWindowList():
                if other is win:
                    continue
                other_rect = other.geometry()
                if dir == 'left' and abs(my_rect.left() - other_rect.right()) < STICKY_DIST and \
                   my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                    if (other, 'right') not in checked:
                        result.append((other, 'right'))
                        dfs(other, dir)
                if dir == 'right' and abs(my_rect.right() - other_rect.left()) < STICKY_DIST and \
                   my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                    if (other, 'left') not in checked:
                        result.append((other, 'left'))
                        dfs(other, dir)
                if dir == 'top' and abs(my_rect.top() - other_rect.bottom()) < STICKY_DIST and \
                   my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                    if (other, 'bottom') not in checked:
                        result.append((other, 'bottom'))
                        dfs(other, dir)
                if dir == 'bottom' and abs(my_rect.bottom() - other_rect.top()) < STICKY_DIST and \
                   my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                    if (other, 'top') not in checked:
                        result.append((other, 'top'))
                        dfs(other, dir)
                if dir == 'left':
                    if abs(my_rect.left() - other_rect.left()) < 2 and \
                       my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                        if (other, 'left') not in checked:
                            result.append((other, 'left'))
                            dfs(other, dir)
                    if abs(my_rect.left() - other_rect.right()) < 2 and \
                       my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                        if (other, 'right') not in checked:
                            result.append((other, 'right'))
                            dfs(other, dir)
                if dir == 'right':
                    if abs(my_rect.right() - other_rect.right()) < 2 and \
                       my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                        if (other, 'right') not in checked:
                            result.append((other, 'right'))
                            dfs(other, dir)
                    if abs(my_rect.right() - other_rect.left()) < 2 and \
                       my_rect.top() < other_rect.bottom() and my_rect.bottom() > other_rect.top():
                        if (other, 'left') not in checked:
                            result.append((other, 'left'))
                            dfs(other, dir)
                if dir == 'top':
                    if abs(my_rect.top() - other_rect.top()) < 2 and \
                       my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                        if (other, 'top') not in checked:
                            result.append((other, 'top'))
                            dfs(other, dir)
                    if abs(my_rect.top() - other_rect.bottom()) < 2 and \
                       my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                        if (other, 'bottom') not in checked:
                            result.append((other, 'bottom'))
                            dfs(other, dir)
                if dir == 'bottom':
                    if abs(my_rect.bottom() - other_rect.bottom()) < 2 and \
                       my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                        if (other, 'bottom') not in checked:
                            result.append((other, 'bottom'))
                            dfs(other, dir)
                    if abs(my_rect.bottom() - other_rect.top()) < 2 and \
                       my_rect.left() < other_rect.right() and my_rect.right() > other_rect.left():
                        if (other, 'top') not in checked:
                            result.append((other, 'top'))
                            dfs(other, dir)
        dfs(self, resize_dir)
        return result

    def mouseMoveEvent(self, event):
        mdi_area = self.getMdiArea()
        if not (self._dragging or self._resizing):
            self.updateCursor(event.pos())
        if mdi_area is None:
            super().mouseMoveEvent(event)
            return
        if self._dragging and self._drag_start_pos:
            new_pos = event.globalPos() - self._drag_start_pos
            new_geom = QRect(new_pos, self.size())
            new_geom = self.stickyRect(new_geom, mdi_area)
            self.move(new_geom.topLeft())
        elif self._resizing and self._drag_start_pos:
            diff = event.globalPos() - self._drag_start_pos
            new_geom = QRect(self._resize_start_rect)
            dir = getattr(self, '_resize_dir', None)
            minw = self.minimumWidth()
            minh = self.minimumHeight()
            adj_all = getattr(self, '_resize_adjacent_all', [])
            if dir:
                if 'left' in dir:
                    new_left = new_geom.left() + diff.x()
                    if new_geom.right() - new_left >= minw:
                        new_geom.setLeft(new_left)
                if 'right' in dir:
                    new_right = new_geom.right() + diff.x()
                    if new_right - new_geom.left() >= minw:
                        new_geom.setRight(new_right)
                if 'top' in dir:
                    new_top = new_geom.top() + diff.y()
                    if new_geom.bottom() - new_top >= minh:
                        new_geom.setTop(new_top)
                if 'bottom' in dir:
                    new_bottom = new_geom.bottom() + diff.y()
                    if new_bottom - new_geom.top() >= minh:
                        new_geom.setBottom(new_bottom)
            new_geom = self.stickyRect(new_geom, mdi_area, resize=True)
            for win, adj_dir in adj_all:
                other_rect = win.geometry()
                ominw = win.minimumWidth()
                ominh = win.minimumHeight()
                if dir == 'right' and adj_dir == 'left':
                    new_left = self.mapToParent(event.pos()).x()
                    fixed_right = other_rect.right()
                    new_width = fixed_right - new_left
                    if new_width >= ominw:
                        other_rect.setLeft(new_left)
                        other_rect.setRight(fixed_right)
                        win.setGeometry(other_rect)
                elif dir == 'left' and adj_dir == 'right':
                    new_right = self.mapToParent(event.pos()).x()
                    fixed_left = other_rect.left()
                    new_width = new_right - fixed_left
                    if new_width >= ominw:
                        other_rect.setLeft(fixed_left)
                        other_rect.setRight(new_right)
                        win.setGeometry(other_rect)
                elif dir == 'bottom' and adj_dir == 'top':
                    new_top = self.mapToParent(event.pos()).y()
                    fixed_bottom = other_rect.bottom()
                    new_height = fixed_bottom - new_top
                    if new_height >= ominh:
                        other_rect.setTop(new_top)
                        other_rect.setBottom(fixed_bottom)
                        win.setGeometry(other_rect)
                elif dir == 'top' and adj_dir == 'bottom':
                    new_bottom = self.mapToParent(event.pos()).y()
                    fixed_top = other_rect.top()
                    new_height = new_bottom - fixed_top
                    if new_height >= ominh:
                        other_rect.setTop(fixed_top)
                        other_rect.setBottom(new_bottom)
                        win.setGeometry(other_rect)
            self.setGeometry(new_geom)
        else:
            super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._resizing = False
        self._resize_dir = None
        self._resize_adjacent = None
        self._drag_start_pos = None
        self._resize_start_rect = None
        super().mouseReleaseEvent(event)

    def isInResizeArea(self, pos):
        margin = 10
        w, h = self.width(), self.height()
        if pos.x() <= margin and pos.y() <= margin:
            return 'topleft'
        if pos.x() >= w - margin and pos.y() <= margin:
            return 'topright'
        if pos.x() <= margin and pos.y() >= h - margin:
            return 'bottomleft'
        if pos.x() >= w - margin and pos.y() >= h - margin:
            return 'bottomright'
        if pos.x() <= margin:
            return 'left'
        if pos.x() >= w - margin:
            return 'right'
        if pos.y() <= margin:
            return 'top'
        if pos.y() >= h - margin:
            return 'bottom'
        return None

    def stickyRect(self, rect, mdi_area, resize=False):
        if mdi_area is None:
            return rect
        for win in mdi_area.subWindowList():
            if win is self:
                continue
            other = win.geometry()
            if abs(rect.top() - other.bottom()) < STICKY_DIST and \
               rect.left() < other.right() and rect.right() > other.left():
                if not resize or (resize and getattr(self, '_resize_dir', '').find('top') != -1):
                    rect.moveTop(other.bottom())
            if abs(rect.bottom() - other.top()) < STICKY_DIST and \
               rect.left() < other.right() and rect.right() > other.left():
                if resize and getattr(self, '_resize_dir', '').find('bottom') != -1:
                    rect.setBottom(other.top())
                elif not resize:
                    rect.moveBottom(other.top())
            if abs(rect.left() - other.right()) < STICKY_DIST and \
               rect.top() < other.bottom() and rect.bottom() > other.top():
                if not resize or (resize and getattr(self, '_resize_dir', '').find('left') != -1):
                    rect.moveLeft(other.right())
            if abs(rect.right() - other.left()) < STICKY_DIST and \
               rect.top() < other.bottom() and rect.bottom() > other.top():
                if resize and getattr(self, '_resize_dir', '').find('right') != -1:
                    rect.setRight(other.left())
                elif not resize:
                    rect.moveRight(other.left())
        area_rect = mdi_area.viewport().rect()
        area_rect.moveTo(0, 0)
        for side, a_side, set_func in [
            (rect.left(), area_rect.left(), rect.moveLeft),
            (rect.top(), area_rect.top(), rect.moveTop),
            (rect.right(), area_rect.right(), rect.setRight),
            (rect.bottom(), area_rect.bottom(), rect.setBottom)
        ]:
            if abs(side - a_side) < STICKY_DIST:
                set_func(a_side)
        return rect

    def getMdiArea(self):
        parent = self.parentWidget()
        while parent is not None:
            if isinstance(parent, QMdiArea):
                return parent
            parent = parent.parentWidget()
        return None

    def updateCursor(self, pos):
        margin = 10
        w, h = self.width(), self.height()
        cursor = None
        if pos.x() <= margin and pos.y() <= margin:
            cursor = Qt.SizeFDiagCursor
        elif pos.x() >= w - margin and pos.y() <= margin:
            cursor = Qt.SizeBDiagCursor
        elif pos.x() <= margin and pos.y() >= h - margin:
            cursor = Qt.SizeBDiagCursor
        elif pos.x() >= w - margin and pos.y() >= h - margin:
            cursor = Qt.SizeFDiagCursor
        elif pos.x() <= margin:
            cursor = Qt.SizeHorCursor
        elif pos.x() >= w - margin:
            cursor = Qt.SizeHorCursor
        elif pos.y() <= margin:
            cursor = Qt.SizeVerCursor
        elif pos.y() >= h - margin:
            cursor = Qt.SizeVerCursor
        else:
            cursor = Qt.ArrowCursor
        self.setCursor(cursor)

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange:
            if self.isMaximized():
                mdi_area = self.getMdiArea()
                if mdi_area is not None:
                    area_rect = mdi_area.viewport().rect()
                    area_rect.moveTo(0, 0)
                    my_rect = self.geometry()
                    left = area_rect.left()
                    right = area_rect.right()
                    top = area_rect.top()
                    bottom = area_rect.bottom()
                    for win in mdi_area.subWindowList():
                        if win is self:
                            continue
                        other = win.geometry()
                        if other.right() <= my_rect.left() and \
                           other.bottom() > my_rect.top() and other.top() < my_rect.bottom():
                            left = max(left, other.right())
                        if other.left() >= my_rect.right() and \
                           other.bottom() > my_rect.top() and other.top() < my_rect.bottom():
                            right = min(right, other.left())
                        if other.bottom() <= my_rect.top() and \
                           other.right() > my_rect.left() and other.left() < my_rect.right():
                            top = max(top, other.bottom())
                        if other.top() >= my_rect.bottom() and \
                           other.right() > my_rect.left() and other.left() < my_rect.right():
                            bottom = min(bottom, other.top())
                    all_adj = True
                    for v, a in zip([left, right, top, bottom], [area_rect.left(), area_rect.right(), area_rect.top(), area_rect.bottom()]):
                        if v == a:
                            all_adj = False
                            break
                    if not all_adj:
                        self.showNormal()
                        self.setGeometry(left, top, right - left, bottom - top)
                        return
        super().changeEvent(event)

    def closeEvent(self, event):
        """サブウィンドウが閉じられる際の処理"""
        # プログラム終了時にはMainWindowがすでに保存処理をするため、
        # ここでは特に何もしない（冗長な保存を避ける）
        try:
            parent = self.getMdiArea().parent()
            widget = self.widget()
            widget_type = ""
            
            if widget:
                if hasattr(widget, 'script_combo') and hasattr(widget, 'script_path'):
                    widget_type = "Python"
                    script = widget.script_path.text() if hasattr(widget, 'script_path') else "(不明)"
                elif hasattr(widget, 'cmdline_combo'):
                    widget_type = "Shell"
                    cmdline = widget.cmdline_combo.currentText() if hasattr(widget, 'cmdline_combo') else "(不明)"
            
            if hasattr(parent, 'in_closing') and parent.in_closing:
                # 終了処理中であれば何もせず閉じる
                debug_print(f"[debug] 終了処理中: {widget_type}サブウィンドウを閉じます")
            else:
                # 個別に閉じる場合は設定を保存
                if hasattr(parent, 'saveAllLaunchers'):
                    if widget_type == "Python":
                        debug_print(f"[debug] 個別閉じる: {widget_type}サブウィンドウ({script})の設定を保存")
                    elif widget_type == "Shell":
                        debug_print(f"[debug] 個別閉じる: {widget_type}サブウィンドウ({cmdline[:20]}...)の設定を保存")
                    else:
                        debug_print(f"[debug] 個別閉じる: 不明なタイプのサブウィンドウの設定を保存")
                    
                    # 親ウィンドウの保存処理を呼び出し
                    parent.saveAllLaunchers()
        except Exception as e:
            error_print(f"[error] サブウィンドウの閉じる処理中にエラー: {e}")
        
        super().closeEvent(event)
