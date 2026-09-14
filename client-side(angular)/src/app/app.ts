import { Component, AfterViewInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { NavbarComponent } from './components/navbar/navbar';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, NavbarComponent],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements AfterViewInit {

  ngAfterViewInit() {
    const loader = document.getElementById('site-loader');
    if (!loader) return;

    setTimeout(() => {
      loader.classList.add('sweeping');

      setTimeout(() => {
        loader.classList.add('done');
        setTimeout(() => loader.remove(), 400);
      }, 1050);
    }, 250);
  }
}
